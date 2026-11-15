"""First-run setup: create private/, draft the profile from a resume, write config.

Works two ways: interactively for a person at a terminal, or from flags so an
agent can run it in one command. It never overwrites an existing profile or
config unless told to.
"""
from __future__ import annotations

import re
import shutil
from pathlib import Path

from jobhunt import config, discover, tracker
from jobhunt.config import ROOT

_EMAIL = re.compile(r"[\w.+-]+@[\w-]+\.[\w.-]+")
_PHONE = re.compile(r"(?:\+?\d{1,3}[\s.-]?)?\(?\d{3}\)?[\s.-]?\d{3}[\s.-]?\d{4}")
_LINKEDIN = re.compile(r"(?:https?://)?(?:www\.)?linkedin\.com/in/[\w%-]+", re.I)
_GITHUB = re.compile(r"(?:https?://)?(?:www\.)?github\.com/[\w-]+", re.I)
_HEADINGS = ["experience", "work experience", "professional experience", "employment",
             "projects", "education", "skills", "technical skills", "additional information",
             "certifications", "summary", "publications", "awards"]


def read_resume(path: Path) -> str:
    if path.suffix.lower() == ".pdf":
        from jobhunt import ats
        return ats.extract_text(path)
    return path.read_text(encoding="utf-8", errors="replace")


def split_sections(text: str) -> dict[str, str]:
    """Cut resume text at standard headings. Text before the first one is 'header'."""
    sections: dict[str, list[str]] = {"header": []}
    current = "header"
    for line in text.splitlines():
        key = re.sub(r"[^a-z ]", "", line.lower()).strip()
        if key in _HEADINGS and len(line.strip()) < 40:
            current = key
            sections.setdefault(current, [])
            continue
        sections[current].append(line.rstrip())
    return {k: "\n".join(v).strip() for k, v in sections.items() if "\n".join(v).strip()}


def _money(v) -> str:
    return f"{v:,.0f}" if isinstance(v, (int, float)) and v else ""


def draft_profile(resume_text: str, answers: dict) -> str:
    """A filled-in profile.md. Everything pulled from the resume is marked for review."""
    sec = split_sections(resume_text) if resume_text else {}
    header = sec.get("header", "")
    first_line = next((ln.strip() for ln in header.splitlines() if ln.strip()), "")
    name = answers.get("name") or (first_line if len(first_line.split()) in (2, 3, 4) else "")

    def grab(rx):
        m = rx.search(resume_text or "")
        return m.group(0) if m else ""

    def block(*keys):
        for k in keys:
            if sec.get(k):
                return sec[k]
        return ""

    titles = answers.get("titles") or []
    lines = [
        "# Profile",
        "",
        "Agents use only the facts in this file and your own resume files. Anything not written",
        "here doesn't exist. Sections marked REVIEW were pulled from your resume by a script:",
        "read them once and fix anything it got wrong.",
        "",
        "## Basics",
        f"- Name: {name}",
        f"- City: {answers.get('city', '')}",
        f"- Email: {grab(_EMAIL)}",
        f"- Phone: {grab(_PHONE)}",
        f"- LinkedIn: {grab(_LINKEDIN)}",
        f"- GitHub: {grab(_GITHUB)}",
        f"- Work authorization: {answers.get('work_auth', '')}  (agents ask you before answering sponsorship questions)",
        f"- Pay floor: {_money(answers.get('pay_floor'))}",
        f"- Pay target: {_money(answers.get('pay_target'))}",
        "",
        "## Targets",
        f"- Titles: {', '.join(titles)}",
        f"- Exclude: {', '.join(answers.get('exclude') or [])}",
        f"- Focus areas: {', '.join(answers.get('boost') or [])}",
        f"- Priority companies (people there can refer you): {', '.join(answers.get('priority') or [])}",
        f"- Countries: {', '.join(answers.get('countries') or [])}; remote: {'yes' if answers.get('remote', True) else 'no'}",
        "",
        "## Experience (REVIEW)",
        block("experience", "work experience", "professional experience", "employment") or "(paste your roles: title, company, dates, one line on the company)",
        "",
        "## Wins and metrics",
        "One line per win: what changed, the number, and where the number comes from.",
        "Only numbers you can defend in an interview.",
        "",
        "## Approved bullets",
        "Bullets you've signed off on, word for word. Agents use these as written.",
        "",
        "## Projects (REVIEW)",
        block("projects") or "(public work only)",
        "",
        "## Tools (REVIEW)",
        block("skills", "technical skills", "additional information") or "(only tools you've really used)",
        "",
        "## Education (REVIEW)",
        block("education") or "(degree, school, graduation year)",
        "",
    ]
    return "\n".join(lines)


def build_config(answers: dict) -> dict:
    """Only the keys the user actually answered; defaults stay in code."""
    cfg: dict = {"mode": answers.get("mode", "lean"), "tracker": answers.get("tracker", "csv")}
    cfg["titles"] = {"include": answers.get("titles") or [], "exclude": answers.get("exclude") or []}
    if answers.get("boost"):
        cfg["keywords"] = {"boost": answers["boost"]}
    loc: dict = {}
    if answers.get("countries"):
        loc["countries"] = [c.upper() for c in answers["countries"]]
    if "remote" in answers:
        loc["remote"] = bool(answers["remote"])
    if answers.get("prefer"):
        loc["prefer"] = answers["prefer"]
    if loc:
        cfg["locations"] = loc
    pay = {k: answers[f"pay_{k}"] for k in ("floor", "target") if answers.get(f"pay_{k}")}
    if pay:
        cfg["pay"] = pay
    if answers.get("priority"):
        cfg["priority_companies"] = answers["priority"]
    if answers.get("sheet_id"):
        cfg["sheet_id"] = answers["sheet_id"]
    if answers.get("name"):
        cfg["files"] = {"name_prefix": "_".join(answers["name"].split())}
    return cfg


def run(answers: dict, *, home: Path, resume: Path | None = None, force: bool = False,
        find_boards: bool = True, log=print) -> dict:
    """Create the private folder, profile, config and tracker. Returns what it did."""
    home.mkdir(parents=True, exist_ok=True)
    done: dict = {"home": str(home), "created": [], "kept": [], "boards": [], "not_found": []}

    resume_text = ""
    if resume:
        resume_text = read_resume(resume)
        if resume.suffix.lower() in (".pdf", ".tex"):
            dest = home / f"resume{resume.suffix.lower()}"
            if force or not dest.exists():
                shutil.copyfile(resume, dest)
                done["created"].append(str(dest))

    profile = home / "profile.md"
    if profile.exists() and not force:
        done["kept"].append(str(profile))
    else:
        profile.write_text(draft_profile(resume_text, answers), encoding="utf-8")
        done["created"].append(str(profile))

    cfg_path = home / "config.json"
    if cfg_path.exists() and not force:
        user_cfg = config.load_user(cfg_path)
        done["kept"].append(str(cfg_path))
    else:
        user_cfg = build_config(answers)
        done["created"].append(str(cfg_path))

    companies = (answers.get("companies") or []) + (answers.get("priority") or [])
    if find_boards:
        for name in dict.fromkeys(companies):
            hits = discover.find(name)
            if not hits:
                done["not_found"].append(name)
                continue
            for hit in hits[:1]:
                discover.add_to_config(user_cfg, name, hit)
                done["boards"].append({"company": name, **hit})
                log(f"  found {name}: {hit['ats']}/{hit['slug']} ({hit['jobs']} jobs, e.g. \"{hit['sample']}\")")
    config.save(user_cfg, cfg_path)

    if user_cfg.get("tracker", "csv") == "csv":
        done["created"] += [str(p) for p in tracker.init(home)]
    example = ROOT / "resume" / "template.tex"
    if not resume and example.exists() and not (home / "resume.tex").exists():
        shutil.copyfile(example, home / "resume.tex")
        done["created"].append(str(home / "resume.tex"))
    return done


def ask(prompt: str, default: str = "") -> str:
    hint = f" [{default}]" if default else ""
    reply = input(f"{prompt}{hint}: ").strip()
    return reply or default


def split_list(s: str) -> list[str]:
    return [x.strip() for x in re.split(r"[,;]", s or "") if x.strip()]


def interview() -> dict:
    """Ask the handful of questions a scan needs."""
    print("A few questions to set up your search. Press Enter to skip any of them.\n")
    a: dict = {}
    a["name"] = ask("Your name")
    a["city"] = ask("Your city")
    a["titles"] = split_list(ask("Job titles to search for, comma-separated (e.g. product manager, senior product manager)"))
    a["exclude"] = split_list(ask("Words that rule a title out", "intern, director, principal, vp"))
    a["boost"] = split_list(ask("Topics you want more of (e.g. healthcare, marketplace, growth)"))
    a["countries"] = split_list(ask("Countries you can work in, as 2-letter codes", "US"))
    a["remote"] = ask("Include remote roles? (y/n)", "y").lower().startswith("y")
    floor = ask("Lowest yearly pay you'd accept (number only)")
    a["pay_floor"] = float(floor.replace(",", "")) if floor.replace(",", "").replace(".", "").isdigit() else None
    a["priority"] = split_list(ask("Companies where someone would refer you"))
    a["companies"] = split_list(ask("Other companies to watch"))
    a["tracker"] = "sheet" if ask("Track in a Google Sheet (needs a connector) or local CSV files? (sheet/csv)", "csv").lower().startswith("s") else "csv"
    a["mode"] = ask("How much should AI agents do? lean / standard / full", "lean").lower()
    if a["mode"] not in config.MODES:
        a["mode"] = "lean"
    return a
