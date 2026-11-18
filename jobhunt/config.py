"""Load and save the user's settings (private/config.json) over sane defaults."""
from __future__ import annotations

import copy
import json
import os
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
MODES = ("lean", "standard", "full")

DEFAULTS: dict = {
    # lean = scripts do everything they can, AI only for jobs you pick
    # standard = an agent also reviews the scan and drafts messages
    # full = an agent evaluates every new job and prepares applications unprompted
    "mode": "lean",
    "tracker": "csv",           # "csv" (no connector needed) or "sheet" (Google Sheets)
    "sheet_id": "",
    "sheet_webhook": "",        # Apps Script web app URL (sheet/README-apps-script.md)
    "sheet_token": "",          # the secret set in that script; keep it private
    "sheet_tab_ids": {"Daily jobs": 1, "Applied": 2, "Network": 3},
    "titles": {
        "include": [],          # phrases; a job title must contain at least one
        "exclude": [],          # words or phrases; a title containing any is dropped
    },
    "keywords": {
        "boost": [],            # terms that raise a job's score (title counts more)
        "require_any": [],      # if set, a job must mention at least `require_min` of these
        "require_min": 1,
        "exclude": [],          # dropped when found in the title or company name
    },
    "locations": {
        "countries": [],        # ISO-2 codes, e.g. ["US", "CA"]; empty = anywhere
        "remote": True,         # keep remote roles open to your countries
        "remote_only": False,
        "prefer": [],           # place names that raise the score, e.g. ["Toronto"]
    },
    "pay": {"floor": None, "target": None},   # yearly, in the currency you're paid in
    "max_age_days": 7,          # skip postings older than this when scanning
    "expire_after_days": 14,    # move unapplied jobs older than this to Archive (0 = never)
    "max_results": 25,
    "max_per_company": 5,       # keeps one big employer from filling the list
    "priority_companies": [],   # scored first: e.g. where someone will refer you
    "big_companies": [],        # recruiter search gets a tech-recruiter filter
    # workday entries are careers-page URLs: {"url": "https://x.wd5.myworkdayjobs.com/Site", "name": "X"}
    "companies": {"greenhouse": [], "lever": [], "ashby": [], "workable": [], "workday": []},
    "sources": {
        "remoteok": True,
        "remotive": True,
        "weworkremotely": [],   # category slugs, e.g. ["remote-product-jobs"]
        "himalayas": True,
        "hackernews": True,
        "amazon": False,
        "jobspy": False,
    },
    "jobspy": {"searches": [], "sites": ["indeed", "linkedin", "zip_recruiter"], "hours_old": 30},
    # manager/peer titles: empty = derived from titles.include
    # company_aliases: extra names for `network find`, e.g. {"Optum": ["optum", "unitedhealth"]}
    "linkedin": {"manager_titles": [], "peer_titles": [], "company_aliases": {}},
    "email_digest": False,      # Google Sheet receiver emails you the top new jobs after each scan
    "email_top": 10,            # how many jobs the email lists
    "files": {"name_prefix": ""},   # e.g. "Ada_Lovelace" -> Ada_Lovelace_Resume_Company.pdf
}


def home() -> Path:
    """Where the user's private files live. Override with JOBHUNT_HOME."""
    return Path(os.environ.get("JOBHUNT_HOME") or ROOT / "private")


def config_path() -> Path:
    return home() / "config.json"


def _merge(base: dict, over: dict) -> dict:
    out = copy.deepcopy(base)
    for k, v in over.items():
        if isinstance(v, dict) and isinstance(out.get(k), dict):
            out[k] = _merge(out[k], v)
        else:
            out[k] = v
    return out


def load(path: Path | None = None) -> dict:
    path = path or config_path()
    user = {}
    if path.exists():
        user = json.loads(path.read_text(encoding="utf-8"))
    cfg = _merge(DEFAULTS, user)
    if cfg["mode"] not in MODES:
        raise ValueError(f"mode must be one of {MODES}, got {cfg['mode']!r}")
    if cfg["tracker"] not in ("csv", "sheet"):
        raise ValueError("tracker must be 'csv' or 'sheet'")
    return cfg


def save(user_cfg: dict, path: Path | None = None) -> Path:
    """Write only what the user set; defaults stay in code so upgrades reach them."""
    path = path or config_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(user_cfg, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return path


def load_user(path: Path | None = None) -> dict:
    path = path or config_path()
    return json.loads(path.read_text(encoding="utf-8")) if path.exists() else {}


def problems(cfg: dict) -> list[str]:
    """Things that would make a scan useless, in plain words."""
    out = []
    if not cfg["titles"]["include"]:
        out.append("No job titles set. Add titles.include, e.g. [\"product manager\"], "
                   "or run: python -m jobhunt init")
    boards = sum(len(v) for v in cfg["companies"].values())
    feeds = [k for k, v in cfg["sources"].items() if v]
    if not boards and not feeds:
        out.append("No sources enabled. Add company boards or turn on a feed in sources.")
    if cfg["tracker"] == "sheet" and not cfg["sheet_id"]:
        out.append("tracker is 'sheet' but sheet_id is empty. Run prompts/create-sheet.md.")
    return out
