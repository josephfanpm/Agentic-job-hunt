"""Company job boards with public JSON feeds: Greenhouse, Lever, Ashby, Workable.

Each parser is a pure function over the decoded payload, so tests can feed it
fixtures. The fetchers make one request per company board.
"""
from __future__ import annotations

import json
from urllib.parse import quote

from jobhunt.models import Job
from jobhunt.text import to_date


def _entry(item) -> tuple[str, str]:
    """A board entry is either "slug" or {"slug": ..., "name": ...}."""
    if isinstance(item, dict):
        return item["slug"], item.get("name") or ""
    return item, ""


def _pretty(slug: str) -> str:
    return slug.replace("-", " ").replace("_", " ").title()


# ---- Greenhouse --------------------------------------------------------------
def greenhouse_url(slug: str, content: bool = True) -> str:
    return f"https://boards-api.greenhouse.io/v1/boards/{quote(slug)}/jobs" + ("?content=true" if content else "")


def parse_greenhouse(payload: dict, name: str = "") -> list[Job]:
    out = []
    for j in payload.get("jobs", []):
        out.append(Job(
            source="greenhouse",
            company=name or j.get("company_name") or "",
            title=j.get("title", ""),
            url=j.get("absolute_url", ""),
            location=(j.get("location") or {}).get("name", "") or "",
            posted=to_date(j.get("first_published") or j.get("updated_at")),
            description=j.get("content", "") or "",
            job_id=str(j.get("id", "")),
        ))
    return out


# ---- Lever -------------------------------------------------------------------
def lever_url(slug: str) -> str:
    return f"https://api.lever.co/v0/postings/{quote(slug)}?mode=json"


def parse_lever(payload: list, name: str = "") -> list[Job]:
    out = []
    for j in payload if isinstance(payload, list) else []:
        cats = j.get("categories") or {}
        locations = cats.get("allLocations") or ([cats["location"]] if cats.get("location") else [])
        workplace = (j.get("workplaceType") or "").lower()
        desc = "\n".join(x for x in (j.get("descriptionPlain"), j.get("additionalPlain")) if x)
        for lst in j.get("lists") or []:
            desc += f"\n{lst.get('text', '')}\n{lst.get('content', '')}"
        out.append(Job(
            source="lever", company=name, title=j.get("text", ""),
            url=j.get("hostedUrl", ""), location="; ".join(locations),
            country=j.get("country") or "",
            remote=True if workplace == "remote" else (False if workplace in ("onsite", "on-site") else None),
            posted=to_date(j.get("createdAt")), description=desc, job_id=str(j.get("id", "")),
        ))
    return out


# ---- Ashby -------------------------------------------------------------------
def ashby_url(slug: str) -> str:
    return f"https://api.ashbyhq.com/posting-api/job-board/{quote(slug)}?includeCompensation=true"


def _ashby_place(loc: str, address: dict | None) -> str:
    postal = (address or {}).get("postalAddress") or {}
    parts = [loc] + [postal.get(k) for k in ("addressRegion", "addressCountry")]
    seen, out = set(), []
    for p in parts:
        if p and p.lower() not in seen:
            seen.add(p.lower())
            out.append(p)
    return ", ".join(out)


def parse_ashby(payload: dict, name: str = "") -> list[Job]:
    out = []
    for j in payload.get("jobs", []):
        if j.get("isListed") is False:
            continue
        places = [_ashby_place(j.get("location", ""), j.get("address"))]
        for s in j.get("secondaryLocations") or []:
            places.append(_ashby_place(s.get("location", ""), s.get("address")))
        comp = j.get("compensation") or {}
        pay_text = comp.get("scrapeableCompensationSalarySummary") or comp.get("compensationTierSummary") or ""
        desc = j.get("descriptionPlain") or j.get("descriptionHtml") or ""
        if pay_text:
            desc = f"{pay_text}\n{desc}"
        workplace = (j.get("workplaceType") or "").lower()
        out.append(Job(
            source="ashby", company=name, title=j.get("title", ""), url=j.get("jobUrl", ""),
            location="; ".join(p for p in places if p),
            # isRemote is also true on hybrid roles, so only workplaceType is trusted
            remote=True if workplace == "remote" else (False if workplace == "onsite" else None),
            posted=to_date(j.get("publishedAt")), description=desc, job_id=str(j.get("id", "")),
        ))
    return out


# ---- Workable ----------------------------------------------------------------
def workable_url(slug: str) -> str:
    return f"https://apply.workable.com/api/v1/widget/accounts/{quote(slug)}?details=true"


def parse_workable(payload: dict, name: str = "") -> list[Job]:
    out = []
    company = payload.get("name") or name
    for j in payload.get("jobs", []):
        place = ", ".join(p for p in (j.get("city"), j.get("state"), j.get("country")) if p)
        out.append(Job(
            source="workable", company=company, title=j.get("title", ""),
            url=j.get("url") or j.get("shortlink", ""), location=place,
            remote=True if j.get("telecommuting") else None,
            posted=to_date(j.get("published_on") or j.get("created_at")),
            description=j.get("description", "") or "", job_id=str(j.get("shortcode", "")),
        ))
    return out


_ATS = {
    "greenhouse": (greenhouse_url, parse_greenhouse),
    "lever": (lever_url, parse_lever),
    "ashby": (ashby_url, parse_ashby),
    "workable": (workable_url, parse_workable),
}


def tasks(cfg: dict):
    """Yield (label, callable(get) -> list[Job]) for every configured board."""
    for ats, (make_url, parse) in _ATS.items():
        for item in cfg["companies"].get(ats, []):
            slug, name = _entry(item)

            def run(get, make_url=make_url, parse=parse, slug=slug, name=name):
                jobs = parse(json.loads(get(make_url(slug), ttl_hours=1)), name)
                for job in jobs:
                    job.company = job.company or _pretty(slug)
                return jobs

            yield f"{ats}:{slug}", run
