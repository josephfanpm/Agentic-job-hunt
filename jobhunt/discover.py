"""Find a company's job board from its name, so nobody hunts for slugs by hand.

Tries a few likely slugs against Greenhouse, Lever, Ashby and Workable. A hit
is a board that answers with at least one job. Slugs aren't unique across the
web, so the result shows a sample job title for the user to sanity-check.
"""
from __future__ import annotations

import json
import re
from concurrent.futures import ThreadPoolExecutor

from jobhunt import net
from jobhunt.sources import boards
from jobhunt.text import norm


def slug_candidates(name: str) -> list[str]:
    words = norm(name).replace("+", " ").replace("#", " ").split()
    if not words:
        return []
    out = ["".join(words), "-".join(words), words[0]]
    trimmed = [w for w in words if w not in ("inc", "llc", "ltd", "corp", "co", "the", "health", "labs")]
    if trimmed and trimmed != words:
        out += ["".join(trimmed), "-".join(trimmed)]
    # some boards carry a country or legal suffix: "doordashusa", "acmeinc"
    out += ["".join(words) + suffix for suffix in ("usa", "inc", "hq")]
    seen, uniq = set(), []
    for s in out:
        s = re.sub(r"[^a-z0-9-]", "", s)
        if s and s not in seen:
            seen.add(s)
            uniq.append(s)
    return uniq


def _probe(ats: str, slug: str, get) -> dict | None:
    url = {"greenhouse": boards.greenhouse_url(slug, content=False), "lever": boards.lever_url(slug),
           "ashby": boards.ashby_url(slug), "workable": boards.workable_url(slug)}[ats]
    try:
        payload = json.loads(get(url, timeout=15, retries=0))
    except (net.FetchError, ValueError):
        return None
    parse = {"greenhouse": boards.parse_greenhouse, "lever": boards.parse_lever,
             "ashby": boards.parse_ashby, "workable": boards.parse_workable}[ats]
    try:
        jobs = parse(payload)
    except (AttributeError, KeyError, TypeError):
        return None
    if not jobs:
        return None
    return {"ats": ats, "slug": slug, "jobs": len(jobs), "sample": jobs[0].title,
            "board_name": jobs[0].company}


def find(name: str, get=net.get) -> list[dict]:
    """Every board that answers for this company name, best guess first."""
    probes = [(ats, slug) for slug in slug_candidates(name)
              for ats in ("greenhouse", "lever", "ashby", "workable")]
    with ThreadPoolExecutor(max_workers=8) as pool:
        hits = [h for h in pool.map(lambda p: _probe(p[0], p[1], get), probes) if h]
    order = {s: i for i, s in enumerate(slug_candidates(name))}
    hits.sort(key=lambda h: (order[h["slug"]], -h["jobs"]))
    # one board per ATS: the earliest slug candidate wins
    seen, out = set(), []
    for h in hits:
        if h["ats"] not in seen:
            seen.add(h["ats"])
            out.append(h)
    return out


def add_to_config(user_cfg: dict, name: str, hit: dict) -> bool:
    """Record a found board in the user's config. False if it was already there."""
    lst = user_cfg.setdefault("companies", {}).setdefault(hit["ats"], [])
    slugs = [e["slug"] if isinstance(e, dict) else e for e in lst]
    if hit["slug"] in slugs:
        return False
    lst.append({"slug": hit["slug"], "name": name})
    return True
