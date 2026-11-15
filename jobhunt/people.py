"""LinkedIn Boolean people searches: recruiters, hiring managers and peers.

Every OR group sits in parentheses before or between ANDs, phrases are quoted,
and each search becomes a one-click LinkedIn URL.
"""
from __future__ import annotations

import re
import urllib.parse

from jobhunt.text import norm_title

RECRUITER = ["recruiter", "talent acquisition", "sourcer"]
BASE = "https://www.linkedin.com/search/results/people/?keywords="
_LEVELS = {"senior", "junior", "lead", "principal", "staff", "associate", "ii", "iii", "iv", "i",
           "manager", "technical", "tech", "remote", "hybrid", "contract", "and", "of", "the",
           "for", "to", "in", "at", "a", "us", "usa", "canada", "global", "team", "level"}


_ROLE_WORDS = {"manager", "engineer", "developer", "designer", "scientist", "analyst",
               "recruiter", "writer", "marketer"}


def term(t: str) -> str:
    return f'"{t}"' if re.search(r"[\s,]", t) else t


def group(items: list[str]) -> str:
    items = [term(t) for t in items if t]
    if not items:
        return ""
    return items[0] if len(items) == 1 else "(" + " OR ".join(items) + ")"


def manager_titles(peer_titles: list[str]) -> list[str]:
    """Likely titles of the person a peer reports to.

    "product manager" -> director of product, head of product, VP of product,
    group product manager... Works for any function whose title ends in a role
    word (manager, engineer, designer, analyst, scientist...).
    """
    out: list[str] = []
    for title in peer_titles[:2]:
        words = norm_title(title).split()
        if not words:
            continue
        function = " ".join(words[:-1])   # "product", "software", "data"; may be empty
        role = words[-1]
        # The discipline a director or VP would be "of"
        field = {"engineer": "engineering", "developer": "engineering", "designer": "design",
                 "scientist": f"{function} science".strip(), "analyst": "analytics",
                 "manager": function, "recruiter": "talent acquisition",
                 "writer": "content", "marketer": "marketing"}.get(role) or function or role
        if role not in _ROLE_WORDS:
            # A title we can't take apart ("registered nurse", "paralegal"): search
            # for whoever manages people with that title.
            candidates = [f"{title} manager", f"{role} manager", f"{title} supervisor",
                          f"{title} lead", f"head of {role}s"]
        elif role == "manager":
            candidates = [f"director of {field}", f"head of {field}", f"VP of {field}",
                          f"group {title}", f"senior manager, {field}"]
        else:
            candidates = [f"director of {field}", f"head of {field}", f"VP of {field}",
                          f"{field} manager", f"{title} manager"]
        for c in candidates:
            if c not in out:
                out.append(c)
    return out[:6]


def team_terms(title: str, include_phrases: list[str]) -> list[str]:
    """Words that name the team, taken from what's left of the title.

    "Senior Product Manager, Seller Onboarding Risk" -> seller, onboarding, risk
    """
    t = norm_title(title)
    for p in sorted(include_phrases, key=len, reverse=True):
        t = f" {t} ".replace(f" {norm_title(p)} ", " ")
    words = [w for w in t.split() if w not in _LEVELS and len(w) > 2 and not w.isdigit()]
    out: list[str] = []
    for w in words:
        if w not in out:
            out.append(w)
    return out[:3]


def searches(company: str | list[str], *, team: list[str] | None = None, big: bool = False,
             peer_titles: list[str] | None = None,
             manager_titles_: list[str] | None = None) -> list[tuple[str, str, str]]:
    """Return [(label, query, url)] for recruiters, hiring managers and peers."""
    peers = peer_titles or ["product manager"]
    managers = manager_titles_ or manager_titles(peers)
    names = company if isinstance(company, list) else [company]
    who = group(names)
    where = group(team or [])

    def join(*parts):
        return " AND ".join(p for p in parts if p)

    rec = [group(RECRUITER)] + (["(product OR tech OR technical)"] if big else []) + [who]
    rows = [("Recruiters", join(*rec)),
            ("Hiring managers", join(group(managers), who, where)),
            ("Peers", join(group(peers), who, where))]
    return [(label, q, BASE + urllib.parse.quote(q, safe="()")) for label, q in rows]


def for_job(company: str, title: str, cfg: dict) -> list[tuple[str, str, str]]:
    """Searches for one job, using the user's config."""
    li = cfg.get("linkedin", {})
    include = cfg["titles"]["include"]
    peers = li.get("peer_titles") or include[:2] or ["product manager"]
    big = any(norm_title(b) == norm_title(company) for b in
              cfg.get("big_companies", []) + cfg.get("priority_companies", []))
    return searches(company, team=team_terms(title, include + peers), big=big, peer_titles=peers,
                    manager_titles_=li.get("manager_titles") or None)


def cell(rows: list[tuple[str, str, str]]) -> dict:
    """A Google Sheets cell: three lines, each a clickable link."""
    text, runs = "", []
    for i, (label, q, url) in enumerate(rows):
        runs.append({"startIndex": len(text), "format": {"link": {"uri": url}}})
        text += f"{label}: {q}" + ("\n" if i < len(rows) - 1 else "")
    return {"userEnteredValue": {"stringValue": text}, "textFormatRuns": runs}


def plain(rows: list[tuple[str, str, str]]) -> str:
    """For CSV trackers and terminals: label, search and link on each line."""
    return "\n".join(f"{label}: {q}\n  {url}" for label, q, url in rows)
