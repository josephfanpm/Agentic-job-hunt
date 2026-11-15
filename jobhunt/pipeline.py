"""Fetch -> filter -> score -> dedupe. Plain rules, no AI calls.

Every decision here is explainable: a job is dropped for a stated reason, and
a kept job carries a `why` sentence built from the rules that matched.
"""
from __future__ import annotations

import datetime as dt
import json
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass, field
from functools import partial
from pathlib import Path

from jobhunt import geo, net, sources
from jobhunt.models import Job
from jobhunt.text import days_ago, drop_boilerplate, has_phrase, norm, norm_title, parse_pay, strip_html

# When the same role shows up twice, keep the copy closest to the employer.
_SOURCE_RANK = ["greenhouse", "lever", "ashby", "workable", "amazon", "himalayas",
                "remotive", "weworkremotely", "remoteok", "hackernews", "jobspy"]
_COMPANY_NOISE = {"inc", "llc", "ltd", "corp", "corporation", "co", "company", "usa", "the",
                  "technologies", "technology", "labs", "hq"}


@dataclass
class ScanResult:
    jobs: list[Job] = field(default_factory=list)
    stats: dict = field(default_factory=dict)      # label -> jobs fetched
    errors: dict = field(default_factory=dict)     # label -> message
    dropped: dict = field(default_factory=dict)    # reason -> count


def job_key(company: str, title: str) -> str:
    c = " ".join(w for w in norm(company).split() if w not in _COMPANY_NOISE)
    return f"{c}|{norm_title(title)}"


# ---- filters -----------------------------------------------------------------
def title_ok(job: Job, cfg: dict) -> str | None:
    """None when the title passes, otherwise the reason it was dropped."""
    t = norm_title(job.title)
    inc = cfg["titles"]["include"]
    if inc and not any(has_phrase(t, p) for p in inc):
        return "title not targeted"
    if any(has_phrase(t, p) for p in cfg["titles"]["exclude"]):
        return "title excluded"
    name = f"{t} {norm(job.company)}"
    if any(has_phrase(name, p) for p in cfg["keywords"]["exclude"]):
        return "keyword excluded"
    return None


def location_ok(job: Job, cfg: dict) -> str | None:
    loc = cfg["locations"]
    remote = job.remote if job.remote is not None else geo.is_remote(job.location)
    if loc["remote_only"] and not remote:
        return "not remote"
    wanted = {c.upper() for c in loc["countries"]}
    if not wanted:
        return None
    found = geo.countries(job.location, job.country)
    if not found:
        job.flags.append("location unverified")
        return None
    if geo.ANY in found or found & wanted:
        if remote and not loc["remote"] and geo.ANY in found:
            return "remote not wanted"
        return None
    return "outside your countries"


def is_priority(job: Job, cfg: dict) -> bool:
    company = norm(job.company)
    return any(norm(c) and has_phrase(company, c) for c in cfg["priority_companies"])


def age_ok(job: Job, cfg: dict, today: dt.date) -> str | None:
    age = days_ago(job.posted, today)
    if age is None:
        job.flags.append("post date unknown")
        return None
    if age > cfg["max_age_days"]:
        # An open role where someone can refer you is worth seeing however old it is
        return None if is_priority(job, cfg) else "too old"
    return None


def role_text(description: str) -> str:
    """The description minus benefits and legal lines, normalized for matching."""
    return norm(drop_boilerplate(description))


# ---- scoring -----------------------------------------------------------------
def score(job: Job, cfg: dict, today: dt.date) -> None:
    """Fill job.score (0-100) and job.why from the config's rules."""
    title = norm_title(job.title)
    body = role_text(job.description)
    points = 50
    reasons: list[str] = []

    boosts = cfg["keywords"]["boost"]
    in_title = [k for k in boosts if has_phrase(title, k)]
    in_body = [k for k in boosts if k not in in_title and has_phrase(body, k)]
    points += min(18, 6 * len(in_title)) + min(16, 2 * len(in_body))
    if in_title or in_body:
        reasons.append("Matches " + ", ".join((in_title + in_body)[:5]))

    if is_priority(job, cfg):
        points += 25
        reasons.append("priority company")

    floor, target = cfg["pay"].get("floor"), cfg["pay"].get("target")
    if job.pay_max is not None:
        if floor and job.pay_max < floor:
            points -= 15
            reasons.append(f"pay tops out below your floor ({job.pay})")
        elif target and job.pay_max >= target:
            points += 8
            reasons.append(f"pay reaches your target ({job.pay})")
        elif floor and job.pay_min is not None and job.pay_min < floor:
            reasons.append(f"pay range starts below your floor ({job.pay})")

    age = days_ago(job.posted, today)
    if age is not None:
        points += 6 if age <= 1 else 4 if age <= 3 else 2 if age <= 7 else 0
        if age > 60:
            reasons.append(f"open since {job.posted}")
        else:
            reasons.append("posted today" if age <= 0 else f"posted {age} day{'s' if age != 1 else ''} ago")

    place = norm(job.location)
    if any(has_phrase(place, p) for p in cfg["locations"]["prefer"]):
        points += 5
        reasons.append("in a preferred location")

    job.score = max(0, min(100, points))
    why = "; ".join(reasons)
    job.why = (why[:1].upper() + why[1:] + ".") if why else "Title match only."
    if job.flags:
        job.why += " Check: " + ", ".join(job.flags) + "."


# ---- seen store --------------------------------------------------------------
def load_seen(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8")) if path.exists() else {}


def save_seen(path: Path, seen: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(seen, indent=0, sort_keys=True), encoding="utf-8")


# ---- the run -----------------------------------------------------------------
def process(raw: list[Job], cfg: dict, seen: dict | None = None,
            today: dt.date | None = None) -> tuple[list[Job], dict]:
    """Filter, score, dedupe and rank already-fetched jobs. Pure; used by tests."""
    today = today or dt.date.today()
    seen = seen or {}
    dropped: dict[str, int] = {}
    best: dict[str, Job] = {}

    def drop(reason: str):
        dropped[reason] = dropped.get(reason, 0) + 1

    for job in raw:
        if not job.title or not job.url:
            drop("missing title or link")
            continue
        reason = title_ok(job, cfg)          # cheapest test first
        if reason:
            drop(reason)
            continue
        job.description = strip_html(job.description)
        reason = location_ok(job, cfg) or age_ok(job, cfg, today)
        if reason:
            drop(reason)
            continue
        req = cfg["keywords"]["require_any"]
        if req:
            hay = f"{norm_title(job.title)} {norm(job.company)} {norm(job.description)}"
            if not any(has_phrase(hay, k) for k in req):
                drop("no required keyword")
                continue
        key = job_key(job.company, job.title)
        if key in seen:
            drop("already seen")
            continue
        if not job.pay:
            job.pay, job.pay_min, job.pay_max = parse_pay(job.description)
        score(job, cfg, today)
        other = best.get(key)
        if other is None or _rank(job) < _rank(other):
            if other is not None:
                drop("duplicate")
            best[key] = job
        else:
            drop("duplicate")

    ranked = sorted(best.values(), key=lambda j: (-j.score, j.company.lower(), j.title.lower()))
    # One employer with many openings shouldn't crowd out everyone else
    jobs, per_company = [], {}
    for job in ranked:
        c = norm(job.company)
        per_company[c] = per_company.get(c, 0) + 1
        if per_company[c] > cfg["max_per_company"]:
            drop("over the per-company limit")
        else:
            jobs.append(job)
    cut = jobs[cfg["max_results"]:]
    if cut:
        dropped["below today's cut-off"] = len(cut)
    return jobs[:cfg["max_results"]], dropped


def _rank(job: Job) -> int:
    base = job.source.split(":")[0]
    return _SOURCE_RANK.index(base) if base in _SOURCE_RANK else len(_SOURCE_RANK)


def run(cfg: dict, *, home: Path, only: set[str] | None = None, include_seen: bool = False,
        remember: bool = True, get=None, today: dt.date | None = None) -> ScanResult:
    """Fetch every enabled source in parallel, then process the lot."""
    today = today or dt.date.today()
    get = get or partial(net.get, cache_dir=home / "cache")
    result = ScanResult()
    raw: list[Job] = []
    tasks = list(sources.all_tasks(cfg, only))

    def call(task):
        label, fn = task
        try:
            return label, fn(get), None
        except Exception as e:  # one broken feed must not stop the scan
            return label, [], f"{type(e).__name__}: {e}"

    with ThreadPoolExecutor(max_workers=6) as pool:
        for label, jobs, err in pool.map(call, tasks):
            result.stats[label] = len(jobs)
            if err:
                result.errors[label] = err
            raw += jobs

    seen_path = home / "state" / "seen.json"
    seen = {} if include_seen else load_seen(seen_path)
    result.jobs, result.dropped = process(raw, cfg, seen, today)
    if remember and result.jobs:
        store = load_seen(seen_path)
        for job in result.jobs:
            store.setdefault(job_key(job.company, job.title), today.isoformat())
        save_seen(seen_path, store)
    return result
