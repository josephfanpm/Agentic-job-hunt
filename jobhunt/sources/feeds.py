"""Open job feeds that aren't tied to one company.

Remote boards (Remote OK, Remotive, We Work Remotely, Himalayas), the monthly
Hacker News "Who is hiring?" thread, Amazon's careers search, and JobSpy as an
optional extra. Parsers are pure functions; fetchers take a `get` callable.

Manners: Remote OK and Remotive ask API users to link back to their listing
and not to hammer the API. Every job keeps the board's own URL, and responses
are cached for hours.
"""
from __future__ import annotations

import json
import re
import xml.etree.ElementTree as ET
from urllib.parse import quote

from jobhunt import geo
from jobhunt.models import Job
from jobhunt.text import norm_title, strip_html, to_date


def _pay_from_numbers(lo, hi, currency: str = "") -> tuple[str, float | None, float | None]:
    try:
        lo, hi = float(lo or 0), float(hi or 0)
    except (TypeError, ValueError):
        return "", None, None
    if lo < 20_000 or hi < lo:
        return "", None, None
    label = f"{currency} " if currency else ""
    return f"{label}{lo:,.0f}–{hi:,.0f}", lo, hi


# ---- Remote OK ---------------------------------------------------------------
REMOTEOK_URL = "https://remoteok.com/api"


def parse_remoteok(payload: list) -> list[Job]:
    out = []
    for j in payload if isinstance(payload, list) else []:
        if not isinstance(j, dict) or "position" not in j:
            continue  # the first element is a legal notice, not a job
        pay, lo, hi = _pay_from_numbers(j.get("salary_min"), j.get("salary_max"), "USD")
        tags = " ".join(j.get("tags") or [])
        out.append(Job(
            source="remoteok", company=(j.get("company") or "").strip(), title=j.get("position", ""),
            url=j.get("url") or j.get("apply_url", ""), location=j.get("location") or "Remote",
            remote=True, posted=to_date(j.get("date") or j.get("epoch")),
            pay=pay, pay_min=lo, pay_max=hi,
            description=f"{tags}\n{j.get('description', '')}", job_id=str(j.get("id", "")),
        ))
    return out


# ---- Remotive ----------------------------------------------------------------
def remotive_url(search: str) -> str:
    return f"https://remotive.com/api/remote-jobs?search={quote(search)}"


def parse_remotive(payload: dict) -> list[Job]:
    out = []
    for j in payload.get("jobs", []):
        salary = j.get("salary") or ""
        out.append(Job(
            source="remotive", company=(j.get("company_name") or "").strip(), title=j.get("title", ""),
            url=j.get("url", ""), location=j.get("candidate_required_location") or "Remote",
            remote=True, posted=to_date(j.get("publication_date")),
            # Salary is free text here ("$35,3k- $52k"); the pipeline parses what it can
            description=f"{salary}\n{j.get('description', '')}", job_id=str(j.get("id", "")),
        ))
    return out


# ---- We Work Remotely (RSS) --------------------------------------------------
def wwr_url(category: str) -> str:
    return f"https://weworkremotely.com/categories/{quote(category)}.rss"


def parse_wwr(xml_bytes: bytes) -> list[Job]:
    out = []
    root = ET.fromstring(xml_bytes)
    for item in root.iter("item"):
        raw = (item.findtext("title") or "").strip()
        company, _, title = raw.partition(": ")
        if not title:
            company, title = "", raw
        out.append(Job(
            source="weworkremotely", company=company.strip(), title=title.strip(),
            url=(item.findtext("link") or item.findtext("guid") or "").strip(),
            location=(item.findtext("region") or "Remote").strip(), remote=True,
            posted=to_date(item.findtext("pubDate")),
            description=f"{item.findtext('skills') or ''}\n{item.findtext('description') or ''}",
        ))
    return out


# ---- Himalayas ---------------------------------------------------------------
def himalayas_url(search: str) -> str:
    return f"https://himalayas.app/jobs/api/search?q={quote(search)}&limit=20"


def parse_himalayas(payload: dict) -> list[Job]:
    out = []
    for j in payload.get("jobs", []):
        pay = lo = hi = None
        if (j.get("salaryPeriod") or "annual") == "annual":
            pay, lo, hi = _pay_from_numbers(j.get("minSalary"), j.get("maxSalary"), j.get("currency") or "")
        places = j.get("locationRestrictions") or []
        out.append(Job(
            source="himalayas", company=j.get("companyName", ""), title=j.get("title", ""),
            url=j.get("applicationLink") or j.get("guid", ""),
            location=", ".join(places) if places else "Worldwide", remote=True,
            posted=to_date(j.get("pubDate")), pay=pay or "", pay_min=lo, pay_max=hi,
            description=j.get("description") or j.get("excerpt") or "", job_id=j.get("guid", ""),
        ))
    return out


# ---- Hacker News "Who is hiring?" --------------------------------------------
HN_STORY_URL = "https://hn.algolia.com/api/v1/search_by_date?tags=story,author_whoishiring&hitsPerPage=10"


def hn_comments_url(story_id: str, phrase: str) -> str:
    return (f"https://hn.algolia.com/api/v1/search_by_date?tags=comment,story_{story_id}"
            f"&query={quote(chr(34) + phrase + chr(34))}&hitsPerPage=100")


def latest_hn_story(payload: dict) -> str:
    for hit in payload.get("hits", []):
        if (hit.get("title") or "").lower().startswith("ask hn: who is hiring"):
            return str(hit["objectID"])
    return ""


def _hn_title(text: str, phrase: str) -> str:
    """Pull the role as written, e.g. 'Senior Product Manager, Growth'."""
    m = re.search(
        rf"((?:[A-Z][\w.&/+-]*\s+){{0,3}})({re.escape(phrase)})((?:\s*[,(–-]\s*|\s+)[A-Z][\w&/+-]*(?:\s+[A-Z][\w&/+-]*){{0,2}}\)?)?",
        text, re.I)
    if not m:
        return phrase.title()
    lead = m.group(1) or ""
    # the lead-in must itself be capitalized words, not the end of a sentence
    lead = " ".join(w for w in lead.split() if w[:1].isupper())
    tail = m.group(3) or ""
    if tail and not re.search(r"[A-Z]", tail):
        tail = ""
    return re.sub(r"\s+", " ", f"{lead} {m.group(2)}{tail}").strip(" ,-–(")


def _short_place(p: str, limit: int = 45) -> str:
    """Trim a header segment that ran on into prose, keeping brackets balanced."""
    if len(p) <= limit:
        return p
    cut = p[:limit]
    if ")" in cut:
        return cut[:cut.rindex(")") + 1]
    if "(" in cut:
        return cut[:cut.index("(")].strip(" ,")
    return cut.rsplit(",", 1)[0].strip() if "," in cut else ""


def parse_hn(payload: dict, story_id: str, phrases: list[str]) -> list[Job]:
    out = []
    for hit in payload.get("hits", []):
        if str(hit.get("parent_id")) != str(story_id):
            continue  # replies to a posting, not a posting
        text = strip_html(hit.get("comment_text") or "")
        first = text.split("\n", 1)[0]
        parts = [p.strip() for p in first.split("|") if p.strip()]
        if not parts:
            continue
        company = re.sub(r"\(?https?://\S+\)?", "", parts[0])
        company = re.sub(r"\(\s*\)", "", company).strip(" -–(") or parts[0]
        if len(company) > 60:
            continue  # free-form prose, not the usual "Company | Role | Location" header
        phrase = next((p for p in phrases if norm_title(p) in norm_title(text)), None)
        if not phrase:
            continue
        place = []
        for p in parts[1:]:
            p = _short_place(p)
            if p and (geo.countries(p) or geo.is_remote(p)):
                place.append(p)
        out.append(Job(
            source="hackernews", company=company, title=_hn_title(text, phrase),
            url=f"https://news.ycombinator.com/item?id={hit['objectID']}",
            location=", ".join(place), remote=True if geo.is_remote(first) else None,
            posted=to_date(hit.get("created_at")), description=text, job_id=str(hit["objectID"]),
        ))
    return out


# ---- Amazon ------------------------------------------------------------------
def amazon_url(phrase: str, countries: list[str]) -> str:
    q = f"https://www.amazon.jobs/en/search.json?base_query={quote(chr(34) + phrase + chr(34))}&result_limit=100&sort=recent"
    for c in countries:
        iso3 = geo.ISO2_TO_ISO3.get(c.upper())
        if iso3:
            q += f"&normalized_country_code%5B%5D={iso3}"
    return q


def parse_amazon(payload: dict) -> list[Job]:
    out = []
    for j in payload.get("jobs", []):
        path = j.get("job_path") or ""
        desc = "\n".join(x for x in (j.get("description"), j.get("basic_qualifications"),
                                     j.get("preferred_qualifications")) if x)
        out.append(Job(
            source="amazon", company="Amazon", title=j.get("title", ""),
            url=f"https://www.amazon.jobs{path}" if path else "",
            location=j.get("normalized_location") or j.get("location") or "",
            country=j.get("country_code") or "",
            posted=to_date(j.get("posted_date")), description=desc, job_id=str(j.get("id_icims", "")),
        ))
    return out


# ---- JobSpy (optional dependency) --------------------------------------------
def fetch_jobspy(cfg: dict) -> list[Job]:
    try:
        from jobspy import scrape_jobs  # type: ignore
    except ImportError as e:
        raise RuntimeError("JobSpy isn't installed. Run: pip install python-jobspy") from e
    opts = cfg["jobspy"]
    out = []
    for s in opts.get("searches", []):
        df = scrape_jobs(site_name=opts.get("sites") or ["indeed"], search_term=s["term"],
                         location=s.get("location", ""), country_indeed=s.get("country", "USA"),
                         hours_old=opts.get("hours_old", 30), results_wanted=s.get("results", 40),
                         linkedin_fetch_description=False)
        for row in df.to_dict("records"):
            def val(k):
                v = row.get(k)
                return "" if v is None or v != v else v  # NaN check
            pay, lo, hi = ("", None, None)
            if val("interval") in ("yearly", ""):
                pay, lo, hi = _pay_from_numbers(val("min_amount"), val("max_amount"), str(val("currency")))
            out.append(Job(
                source=f"jobspy:{val('site')}", company=str(val("company")), title=str(val("title")),
                url=str(val("job_url")), location=str(val("location")),
                remote=True if val("is_remote") is True else None,
                posted=to_date(str(val("date_posted"))[:10]), pay=pay, pay_min=lo, pay_max=hi,
                description=str(val("description")),
            ))
    return out


def tasks(cfg: dict):
    """Yield (label, callable(get) -> list[Job]) for every enabled feed."""
    src = cfg["sources"]
    phrases = cfg["titles"]["include"]
    if src.get("remoteok"):
        yield "remoteok", lambda get: parse_remoteok(json.loads(get(REMOTEOK_URL, ttl_hours=2)))
    if src.get("remotive"):
        for p in phrases:
            yield f"remotive:{p}", lambda get, p=p: parse_remotive(json.loads(get(remotive_url(p), ttl_hours=6)))
    for cat in src.get("weworkremotely") or []:
        yield f"weworkremotely:{cat}", lambda get, cat=cat: parse_wwr(get(wwr_url(cat), ttl_hours=2))
    if src.get("himalayas"):
        for p in phrases:
            yield f"himalayas:{p}", lambda get, p=p: parse_himalayas(json.loads(get(himalayas_url(p), ttl_hours=2)))
    if src.get("hackernews"):
        def hn(get):
            story = latest_hn_story(json.loads(get(HN_STORY_URL, ttl_hours=12)))
            if not story:
                return []
            jobs = []
            for p in phrases:
                jobs += parse_hn(json.loads(get(hn_comments_url(story, p), ttl_hours=2)), story, phrases)
            return jobs
        yield "hackernews", hn
    if src.get("amazon"):
        countries = cfg["locations"]["countries"]
        for p in phrases:
            yield f"amazon:{p}", lambda get, p=p: parse_amazon(json.loads(get(amazon_url(p, countries), ttl_hours=2)))
    if src.get("jobspy"):
        yield "jobspy", lambda get: fetch_jobspy(cfg)
