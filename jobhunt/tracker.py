"""A CSV tracker: the same three tabs as the Google Sheet, as local files.

It needs no connector and no AI calls, so the daily scan can run from a plain
scheduled task. The files open in Excel or import into Google Sheets.
"""
from __future__ import annotations

import csv
import datetime as dt
from pathlib import Path

from jobhunt import people, sheet
from jobhunt.models import Job
from jobhunt.text import norm, norm_title

FILES = {"Daily jobs": "daily_jobs.csv", "Applied": "applied.csv", "Network": "network.csv"}
OPEN_STATUSES = {"applied", "referral requested", "recruiter screen", "interviewing"}


def folder(home: Path) -> Path:
    return home / "tracker"


def path(home: Path, tab: str) -> Path:
    return folder(home) / FILES[tab]


def headers(tab: str) -> list[str]:
    return [c["name"] for c in sheet.columns(tab)]


def init(home: Path) -> list[Path]:
    """Create any tracker file that doesn't exist yet. Never overwrites."""
    made = []
    folder(home).mkdir(parents=True, exist_ok=True)
    for tab in FILES:
        p = path(home, tab)
        if not p.exists():
            with p.open("w", newline="", encoding="utf-8-sig") as f:
                csv.writer(f).writerow(headers(tab))
            made.append(p)
    return made


def read(home: Path, tab: str) -> list[dict]:
    p = path(home, tab)
    if not p.exists():
        return []
    with p.open(newline="", encoding="utf-8-sig") as f:
        return list(csv.DictReader(f))


def write(home: Path, tab: str, rows: list[dict]) -> None:
    init(home)
    with path(home, tab).open("w", newline="", encoding="utf-8-sig") as f:
        w = csv.DictWriter(f, fieldnames=headers(tab), extrasaction="ignore")
        w.writeheader()
        w.writerows(rows)


def add_jobs(home: Path, jobs: list[Job], cfg: dict, today: dt.date | None = None) -> int:
    """Put today's jobs at the top of daily_jobs.csv, like the sheet does."""
    if not jobs:
        return 0
    new = []
    for rank, job in enumerate(jobs, start=1):
        v = sheet.job_values(job, rank, cfg, today)
        v["Applied"] = "FALSE"
        v["LinkedIn search"] = "\n".join(f"{label}: {url}" for label, _, url in v["LinkedIn search"])
        new.append(v)
    write(home, "Daily jobs", new + read(home, "Daily jobs"))
    return len(new)


def _same(row: dict, company: str, role: str) -> bool:
    return norm(row.get("Company")) == norm(company) and norm_title(row.get("Role")) == norm_title(role)


def find_job(home: Path, query: str) -> list[dict]:
    """Daily-jobs rows whose company or role contains the query."""
    q = norm(query)
    return [r for r in read(home, "Daily jobs")
            if q in norm(r.get("Company")) or q in norm(r.get("Role"))]


def mark_applied(home: Path, company: str, role: str, *, channel: str = "Cold application",
                 resume: str = "", contacts: str = "", notes: str = "",
                 today: dt.date | None = None, follow_up_days: int = 7) -> dict:
    """Tick the job in Daily jobs and log it in Applied with a follow-up date."""
    today = today or dt.date.today()
    daily = read(home, "Daily jobs")
    source = next((r for r in daily if _same(r, company, role)), None)
    if source:
        source["Applied"] = "TRUE"
        write(home, "Daily jobs", daily)
    applied = read(home, "Applied")
    if any(_same(r, company, role) for r in applied):
        raise ValueError(f"{company} / {role} is already in the Applied tracker")
    row = {
        "Applied date": today.isoformat(), "Company": company, "Role": role,
        "Pay": (source or {}).get("Pay", ""), "Location": (source or {}).get("Location", ""),
        "Status": "Applied", "Contacts messaged": contacts,
        "Follow up on": (today + dt.timedelta(days=follow_up_days)).isoformat(),
        "Resume sent": resume, "Notes": notes, "Link": (source or {}).get("Link", ""),
        "Channel": channel,
    }
    write(home, "Applied", [row] + applied)
    return row


def due(home: Path, today: dt.date | None = None) -> list[dict]:
    """Applications and contacts whose follow-up date has arrived."""
    today = (today or dt.date.today()).isoformat()
    out = []
    for r in read(home, "Applied"):
        when = r.get("Follow up on", "")
        if when and when <= today and (r.get("Status", "").lower() in OPEN_STATUSES):
            out.append({"kind": "application", "who": f"{r['Company']} — {r['Role']}",
                        "since": r.get("Applied date", ""), "due": when,
                        "contacts": r.get("Contacts messaged", "")})
    for r in read(home, "Network"):
        sent = r.get("Messaged on", "")
        if not sent or r.get("Status", "").lower() != "messaged":
            continue
        try:
            when = (dt.date.fromisoformat(sent) + dt.timedelta(days=7)).isoformat()
        except ValueError:
            continue
        if when <= today:
            out.append({"kind": "contact", "who": f"{r.get('Name', '')} ({r.get('Company', '')})",
                        "since": sent, "due": when, "contacts": ""})
    return sorted(out, key=lambda x: x["due"])


def channel_stats(home: Path) -> list[dict]:
    """Applications and interviews per channel: which route actually works."""
    stats: dict[str, dict] = {}
    for r in read(home, "Applied"):
        ch = r.get("Channel") or "Unknown"
        s = stats.setdefault(ch, {"channel": ch, "applied": 0, "interviews": 0, "offers": 0})
        s["applied"] += 1
        status = r.get("Status", "").lower()
        if status in ("recruiter screen", "interviewing", "offer"):
            s["interviews"] += 1
        if status == "offer":
            s["offers"] += 1
    return sorted(stats.values(), key=lambda s: -s["applied"])


def searches_text(company: str, role: str, cfg: dict) -> str:
    return people.plain(people.for_job(company, role, cfg))
