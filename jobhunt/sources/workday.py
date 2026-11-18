"""Workday careers sites (*.myworkdayjobs.com), read through the JSON the site itself loads.

Many large employers (health insurers, hospital systems, banks) post only on
Workday, which has no public feed. Each careers page loads its listings from
`/wday/cxs/<tenant>/<site>/jobs` (a POST with a search) and each posting from
`/wday/cxs/<tenant>/<site>/job/...`. No login, no browser, no AI.

Workday's search text is loose: on some sites it matches any word anywhere in
the posting, and results come newest first. So the scan pages through the
listing, keeps titles that pass your title rules, and fetches the full posting
only for those. It stops early once a whole page is older than max_age_days.

Config entry: {"url": "https://cigna.wd5.myworkdayjobs.com/cignacareers", "name": "Cigna"}
Optional per entry:
- "categories": job-category names to filter by, e.g. ["Product", "Technology"]. Matched
  against the site's own category filter (any name containing the text). Big sites with
  thousands of postings need this; `jobhunt boards add <url>` lists the names.
- "search" (default: your title phrases), "max_pages" (default 25, 20 postings a page),
  "max_details" (default 40 full postings).
"""
from __future__ import annotations

import datetime as dt
import json
import re
import threading
import time
from urllib.parse import urlparse

from jobhunt import net

from jobhunt.models import Job
from jobhunt.text import to_date

PAGE = 20                 # Workday refuses larger pages
MAX_PAGES = 25
MAX_DETAILS = 40
_LOCALE = re.compile(r"^[a-z]{2}-[A-Z]{2}$")
# Workday rate-limits per data center (wd1, wd3, wd5...), not per company, so sites
# that share one take turns instead of running in parallel.
_DC_LOCKS: dict[str, threading.Lock] = {}
_DC_GUARD = threading.Lock()


def _dc_lock(host: str) -> threading.Lock:
    dc = ".".join(host.split(".")[1:]) or host
    with _DC_GUARD:
        return _DC_LOCKS.setdefault(dc, threading.Lock())


class WorkdayURLError(ValueError):
    pass


def parse_site(url: str) -> dict:
    """Split a careers URL into host, tenant and site.

    Accepts what people paste from the browser: with or without https://, a
    locale (/en-US/), or a job path after the site name. Also handles the
    *.myworkdaysite.com/recruiting/<tenant>/<site> form.
    """
    url = url.strip()
    if "://" not in url:
        url = "https://" + url
    u = urlparse(url)
    host = (u.hostname or "").lower()
    parts = [p for p in u.path.split("/") if p and not _LOCALE.match(p)]
    if host.endswith(".myworkdayjobs.com") and parts:
        return {"host": host, "tenant": host.split(".")[0], "site": parts[0], "prefix": f"/{parts[0]}"}
    if host.endswith(".myworkdaysite.com") and len(parts) >= 3 and parts[0] == "recruiting":
        return {"host": host, "tenant": parts[1], "site": parts[2], "prefix": f"/recruiting/{parts[1]}/{parts[2]}"}
    raise WorkdayURLError(
        f"{url}: not a Workday careers URL. Open the company's careers page and copy the address "
        "once it shows the job list, e.g. https://cigna.wd5.myworkdayjobs.com/cignacareers")


def api_base(site: dict) -> str:
    return f"https://{site['host']}/wday/cxs/{site['tenant']}/{site['site']}"


def search_body(text: str, offset: int, facets: dict | None = None, limit: int = PAGE) -> bytes:
    return json.dumps({"appliedFacets": facets or {}, "limit": limit, "offset": offset,
                       "searchText": text}, sort_keys=True).encode()


def category_facets(payload: dict) -> dict[str, list[dict]]:
    """{facetParameter: [{"name", "id", "count"}]} for the site's job-category style filters."""
    out: dict[str, list[dict]] = {}

    def walk(facets):
        for f in facets or []:
            label = (f.get("descriptor") or "").lower()
            param = f.get("facetParameter") or ""
            vals = f.get("values") or []
            if any("values" in v for v in vals):
                walk(vals)
                continue
            if param and ("categor" in label or "famil" in label or "famil" in param.lower()):
                out[param] = [{"name": v.get("descriptor", ""), "id": v.get("id", ""),
                               "count": v.get("count")} for v in vals if v.get("id")]
    walk(payload.get("facets"))
    return out


def pick_facets(payload: dict, wanted: list[str]) -> dict:
    """appliedFacets for the category names asked for. Raises if none match."""
    applied: dict[str, list[str]] = {}
    for param, vals in category_facets(payload).items():
        ids = [v["id"] for v in vals if any(w.lower() in v["name"].lower() for w in wanted)]
        if ids:
            applied[param] = ids
    if not applied:
        names = sorted({v["name"] for vals in category_facets(payload).values() for v in vals})
        raise ValueError(f"no job category matches {wanted}; this site has: {', '.join(names) or 'none'}")
    return applied


def posted_days(text: str) -> int | None:
    """'Posted Today' -> 0, 'Posted Yesterday' -> 1, 'Posted 30+ Days Ago' -> 30."""
    t = (text or "").lower()
    if "today" in t:
        return 0
    if "yesterday" in t:
        return 1
    m = re.search(r"(\d+)\+?\s*day", t)
    return int(m.group(1)) if m else None


def parse_listing(payload: dict) -> tuple[int, list[dict]]:
    """(total, postings) from one search page."""
    return int(payload.get("total") or 0), list(payload.get("jobPostings") or [])


def _posted_from_days(text: str, today: dt.date) -> str:
    days = posted_days(text)
    return (today - dt.timedelta(days=days)).isoformat() if days is not None and days < 30 else ""


def from_listing(p: dict, site: dict, name: str, today: dt.date) -> Job:
    """A job from the search page alone, used when its full posting won't load."""
    path = p.get("externalPath") or ""
    loc = p.get("locationsText") or ""
    job = Job(source="workday", company=name or site["tenant"].title(), title=p.get("title", ""),
              url=f"https://{site['host']}{site['prefix']}{path}",
              location="" if re.match(r"^\d+ locations?$", loc, re.I) else loc,
              posted=_posted_from_days(p.get("postedOn", ""), today),
              job_id=str((p.get("bulletFields") or [""])[0]))
    job.flags.append("description not loaded")
    return job


def parse_detail(payload: dict, site: dict, name: str, external_path: str,
                 today: dt.date | None = None) -> Job:
    info = payload.get("jobPostingInfo") or {}
    today = today or dt.date.today()
    places = [info.get("location") or ""] + list(info.get("additionalLocations") or [])
    places = [p for p in places if p]
    country = ""
    if len(places) <= 1:   # the requisition's country is only safe for a single-location job
        country = ((info.get("jobRequisitionLocation") or {}).get("country") or {}).get("alpha2Code") or ""
    posted = to_date(info.get("startDate") or "") or _posted_from_days(info.get("postedOn", ""), today)
    remote_type = (info.get("remoteType") or "").lower()
    url = info.get("externalUrl") or f"https://{site['host']}{site['prefix']}{external_path}"
    company = name or (payload.get("hiringOrganization") or {}).get("name") or site["tenant"].title()
    return Job(
        source="workday", company=company, title=info.get("title", ""), url=url,
        location="; ".join(places), country=country,
        remote=True if remote_type == "remote" else (False if remote_type in ("on-site", "onsite") else None),
        posted=posted, description=info.get("jobDescription", "") or "",
        job_id=str(info.get("jobReqId") or info.get("jobPostingId") or ""),
    )


def fetch(entry: dict, cfg: dict, get, today: dt.date | None = None, pause: float = 0.5) -> list[Job]:
    """Every posting on one Workday site whose title passes the title rules."""
    site = parse_site(entry["url"])
    with _dc_lock(site["host"]):
        return _fetch(entry, site, cfg, get, today or dt.date.today(), pause)


def _fetch(entry: dict, site: dict, cfg: dict, get, today: dt.date, pause: float) -> list[Job]:
    from jobhunt.pipeline import is_priority, title_ok   # late import: pipeline imports sources

    def call(url, **kw):
        if pause and calls[0]:
            time.sleep(pause)   # Workday answers bursts with HTTP 429
        calls[0] += 1
        return get(url, retries=2, **kw)
    calls = [0]

    name = entry.get("name", "")
    base = api_base(site)
    text = entry.get("search") or " ".join(dict.fromkeys(cfg["titles"]["include"]))
    max_pages = int(entry.get("max_pages") or MAX_PAGES)
    max_details = int(entry.get("max_details") or MAX_DETAILS)
    max_age = cfg["max_age_days"]
    probe = Job(source="workday", company=name, title="", url="")
    keep_old = bool(name) and is_priority(probe, cfg)   # referral companies skip the age filter

    facets = {}
    if entry.get("categories"):
        first = json.loads(call(f"{base}/jobs", data=search_body("", 0, limit=1), ttl_hours=24))
        facets = pick_facets(first, list(entry["categories"]))

    wanted: dict[str, dict] = {}
    offset, total = 0, None
    newest_first, last_age = True, 0
    for page in range(max_pages):
        body = search_body(text, offset, facets)
        try:
            total, postings = parse_listing(json.loads(call(f"{base}/jobs", data=body, ttl_hours=1)))
        except net.FetchError:
            if page == 0:
                raise
            break   # rate limited partway: keep what the earlier pages found
        if not postings:
            break
        ages = []
        for p in postings:
            days = posted_days(p.get("postedOn", ""))
            ages.append(days)
            if days is not None and days > max_age and not keep_old:
                continue
            path = p.get("externalPath") or ""
            probe.title = p.get("title", "")
            if path and not title_ok(probe, cfg):
                wanted.setdefault(path, p)
        offset += len(postings)
        if offset >= total:
            break
        # Some sites list newest first, others by relevance. Stop early only on the first kind.
        known = [a for a in ages if a is not None]
        if known != sorted(known) or (known and known[0] < last_age):
            newest_first = False
        last_age = known[-1] if known else last_age
        if newest_first and not keep_old and known and len(known) == len(ages) and known[0] > max_age:
            break   # this whole page is older than max_age_days, and so is everything after it

    jobs = []
    for path in list(wanted)[:max_details]:
        try:
            jobs.append(parse_detail(json.loads(call(f"{base}{path}", ttl_hours=6)), site, name, path, today))
        except (net.FetchError, ValueError):
            jobs.append(from_listing(wanted[path], site, name, today))   # one bad posting can't sink the site
    return jobs


def tasks(cfg: dict):
    for entry in cfg["companies"].get("workday", []):
        if isinstance(entry, str):
            entry = {"url": entry}
        try:
            site = parse_site(entry["url"])
            label = f"workday:{site['tenant']}/{site['site']}"
        except WorkdayURLError:
            label = f"workday:{entry.get('url', '?')}"
        yield label, lambda get, entry=entry: fetch(entry, cfg, get)


def is_workday_url(text: str) -> bool:
    return bool(re.search(r"\.myworkday(jobs|site)\.com", text or "", re.I))


def probe(url: str, get) -> dict:
    """Check a careers URL answers. Returns the clean URL, job count and a sample title."""
    site = parse_site(url)
    payload = json.loads(get(f"{api_base(site)}/jobs", data=search_body("", 0), timeout=15, retries=2))
    total, postings = parse_listing(payload)
    cats = [v for vals in category_facets(payload).values() for v in vals]
    return {"url": f"https://{site['host']}{site['prefix']}", "tenant": site["tenant"], "jobs": total,
            "sample": postings[0].get("title", "") if postings else "", "categories": cats}


def add_to_config(user_cfg: dict, name: str, url: str) -> bool:
    """Record a Workday site in the user's config. False if it was already there."""
    lst = user_cfg.setdefault("companies", {}).setdefault("workday", [])
    key = parse_site(url)
    for e in lst:
        try:
            other = parse_site(e["url"] if isinstance(e, dict) else e)
        except WorkdayURLError:
            continue
        if (other["host"], other["site"].lower()) == (key["host"], key["site"].lower()):
            return False
    lst.append({"url": url, "name": name})
    return True
