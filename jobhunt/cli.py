"""Command line: python -m jobhunt <command>. Run with --help for the list."""
from __future__ import annotations

import argparse
import datetime as dt
import json
import re
import sys
from pathlib import Path

from jobhunt import __version__, config


def _utf8():
    for stream in (sys.stdout, sys.stderr):
        try:
            stream.reconfigure(encoding="utf-8", errors="replace")
        except (AttributeError, ValueError):
            pass


def _slug(s: str) -> str:
    return re.sub(r"[^A-Za-z0-9]+", "_", s).strip("_")[:60]


def _load(args) -> tuple[dict, Path]:
    home = Path(args.home) if getattr(args, "home", None) else config.home()
    return config.load(home / "config.json"), home


# ---- init --------------------------------------------------------------------
def cmd_init(args) -> int:
    from jobhunt import wizard
    home = Path(args.home) if args.home else config.home()
    flags = {k: getattr(args, k) for k in ("titles", "exclude", "boost", "countries", "priority",
                                           "companies", "name", "city", "pay_floor", "pay_target",
                                           "tracker", "mode", "sheet_id")}
    given = any(v not in (None, [], "") for v in flags.values())
    if given or args.yes or not sys.stdin.isatty():
        answers = {k: v for k, v in flags.items() if v not in (None, "")}
        for k in ("titles", "exclude", "boost", "countries", "priority", "companies"):
            if isinstance(answers.get(k), str):
                answers[k] = wizard.split_list(answers[k])
        if args.no_remote:
            answers["remote"] = False
    else:
        answers = wizard.interview()
    done = wizard.run(answers, home=home, resume=Path(args.resume) if args.resume else None,
                      force=args.force, find_boards=not args.no_boards)
    for p in done["created"]:
        print(f"created  {p}")
    for p in done["kept"]:
        print(f"kept     {p}  (already there; use --force to replace)")
    for name in done["not_found"]:
        print(f"no public job board found for {name}; it may use another system")
    cfg = config.load(home / "config.json")
    for msg in config.problems(cfg):
        print(f"todo: {msg}")
    print("\nNext: review private/profile.md, then run: python -m jobhunt scan")
    return 0


# ---- scan --------------------------------------------------------------------
def cmd_scan(args) -> int:
    from jobhunt import pipeline, sheet, tracker
    cfg, home = _load(args)
    issues = config.problems(cfg)
    if any("titles" in m or "sources" in m for m in issues):
        for m in issues:
            print(f"cannot scan: {m}")
        return 2
    if args.limit:
        cfg["max_results"] = args.limit
    only = set(args.sources.split(",")) if args.sources else None
    today = dt.date.today()
    res = pipeline.run(cfg, home=home, only=only, include_seen=args.include_seen,
                       remember=not args.dry_run, today=today)

    out_dir = home / "out"
    out_dir.mkdir(parents=True, exist_ok=True)
    scan_file = out_dir / f"scan-{today.isoformat()}.json"
    scan_file.write_text(json.dumps({
        "date": today.isoformat(), "jobs": [j.to_dict() for j in res.jobs],
        "fetched": res.stats, "errors": res.errors, "dropped": res.dropped,
    }, indent=1, ensure_ascii=False), encoding="utf-8")

    # Keep each job description, so nobody has to fetch it again to tailor
    jd_dir = home / "jds"
    jd_dir.mkdir(exist_ok=True)
    for j in res.jobs:
        if j.description:
            (jd_dir / f"{_slug(j.company)}__{_slug(j.title)}.txt").write_text(
                f"{j.title}\n{j.company}\n{j.url}\n\n{j.description}", encoding="utf-8")

    fetched = sum(res.stats.values())
    print(f"{fetched} postings read from {len(res.stats)} source(s); {len(res.jobs)} new match(es).")
    if res.dropped:
        print("dropped: " + ", ".join(f"{n} {why}" for why, n in sorted(res.dropped.items(), key=lambda x: -x[1])))
    for label, err in res.errors.items():
        print(f"source failed: {label}: {err}")
    for i, j in enumerate(res.jobs, start=1):
        pay = f" | {j.pay}" if j.pay else ""
        print(f"{i:>2}. [{j.score}] {j.company} — {j.title} | {j.location or 'location not given'}{pay}")
        print(f"    {j.why}  {j.url}")

    if args.dry_run:
        print("\ndry run: nothing was added to your tracker.")
    elif res.jobs and cfg["tracker"] == "csv":
        n = tracker.add_jobs(home, res.jobs, cfg, today)
        print(f"\nadded {n} row(s) to {tracker.path(home, 'Daily jobs')}")
    elif res.jobs:
        req_file = out_dir / f"sheet-rows-{today.isoformat()}.json"
        req_file.write_text(json.dumps(sheet.row_requests(res.jobs, cfg, today), separators=(",", ":"),
                                       ensure_ascii=False), encoding="utf-8")
        print(f"\nsheet update ready: {req_file}")
        print(f"send it as one batchUpdate to spreadsheet {cfg['sheet_id']}")
    print(f"details: {scan_file}")
    return 1 if res.errors and not res.jobs and not fetched else 0


# ---- check -------------------------------------------------------------------
def cmd_check(args) -> int:
    from jobhunt import ats
    jd = Path(args.jd).read_text(encoding="utf-8", errors="replace") if args.jd else None
    company = args.company or ""
    if jd and not company:
        head = jd.splitlines()[:3]   # files saved by `scan` start: title, company, link
        if len(head) == 3 and head[2].startswith("http"):
            company = head[1].strip()
    rep = ats.check(args.pdf, max_pages=args.max_pages, jd_text=jd, letter=args.letter, company=company)
    print(ats.render(rep))
    return 0 if rep.ok else 1


# ---- people ------------------------------------------------------------------
def cmd_people(args) -> int:
    from jobhunt import people
    cfg, _ = _load(args)
    if args.peer:
        cfg["linkedin"]["peer_titles"] = args.peer
    if args.big:
        cfg["big_companies"] = cfg["big_companies"] + [args.company]
    print(people.plain(people.for_job(args.company, args.title or "", cfg)))
    return 0


# ---- boards ------------------------------------------------------------------
def cmd_boards(args) -> int:
    from jobhunt import discover
    cfg, home = _load(args)
    if args.action == "list":
        for ats_name, lst in cfg["companies"].items():
            for e in lst:
                slug, name = (e["slug"], e.get("name", "")) if isinstance(e, dict) else (e, "")
                print(f"{ats_name:<11} {slug:<28} {name}")
        return 0
    user = config.load_user(home / "config.json")
    for name in args.names:
        hits = discover.find(name)
        if not hits:
            print(f"{name}: no public board found on Greenhouse, Lever, Ashby or Workable")
            continue
        hit = hits[0]
        added = discover.add_to_config(user, name, hit)
        print(f"{name}: {hit['ats']}/{hit['slug']}, {hit['jobs']} jobs, e.g. \"{hit['sample']}\""
              + ("" if added else "  (already tracked)"))
        for other in hits[1:]:
            print(f"    also answers on {other['ats']}/{other['slug']} ({other['jobs']} jobs); not added")
    config.save(user, home / "config.json")
    print("Check each sample title looks like the right company; remove wrong ones from private/config.json.")
    return 0


# ---- sheet -------------------------------------------------------------------
def cmd_sheet(args) -> int:
    from jobhunt import sheet
    print(json.dumps(sheet.create_requests(args.rows), separators=(",", ":")))
    return 0


# ---- tracker commands --------------------------------------------------------
def cmd_applied(args) -> int:
    from jobhunt import tracker
    cfg, home = _load(args)
    if cfg["tracker"] != "csv":
        print("Your tracker is a Google Sheet; ask your agent to log this (prompts/apply.md).")
        return 2
    company, role = args.company, args.role
    if not role:
        matches = tracker.find_job(home, company)
        if len(matches) != 1:
            print(f"{len(matches)} jobs match '{company}'. Give the role too: applied \"Company\" \"Role\"")
            for m in matches[:8]:
                print(f"  {m['Company']} — {m['Role']}")
            return 2
        company, role = matches[0]["Company"], matches[0]["Role"]
    try:
        row = tracker.mark_applied(home, company, role, channel=args.channel, resume=args.resume or "",
                                   contacts=args.contacts or "", notes=args.notes or "")
    except ValueError as e:
        print(e)
        return 2
    print(f"logged {company} — {role} via {row['Channel']}; follow up on {row['Follow up on']}")
    return 0


def cmd_due(args) -> int:
    from jobhunt import tracker
    cfg, home = _load(args)
    if cfg["tracker"] != "csv":
        print("Your tracker is a Google Sheet; ask your agent to run prompts/follow-up.md.")
        return 2
    items = tracker.due(home)
    if not items:
        print("Nothing to follow up on today.")
        return 0
    for it in items:
        extra = f" (messaged: {it['contacts']})" if it["contacts"] else ""
        print(f"{it['due']}  {it['kind']:<11} {it['who']}  since {it['since']}{extra}")
    return 0


def cmd_stats(args) -> int:
    from jobhunt import tracker
    cfg, home = _load(args)
    if cfg["tracker"] != "csv":
        print("Your tracker is a Google Sheet; ask your agent to run prompts/review.md.")
        return 2
    rows = tracker.channel_stats(home)
    if not rows:
        print("No applications logged yet.")
        return 0
    print(f"{'Channel':<26}{'Applied':>8}{'Interviews':>12}{'Rate':>7}{'Offers':>8}")
    for s in rows:
        rate = f"{100 * s['interviews'] / s['applied']:.0f}%" if s["applied"] else "-"
        print(f"{s['channel']:<26}{s['applied']:>8}{s['interviews']:>12}{rate:>7}{s['offers']:>8}")
    total = sum(s["applied"] for s in rows)
    if total < 20:
        print(f"\nOnly {total} application{'s' if total != 1 else ''} so far: too few to compare channels reliably.")
    return 0


# ---- mode / doctor -----------------------------------------------------------
def cmd_mode(args) -> int:
    cfg, home = _load(args)
    if not args.name:
        print(f"mode: {cfg['mode']}   tracker: {cfg['tracker']}   (see MODES.md)")
        return 0
    user = config.load_user(home / "config.json")
    user["mode"] = args.name
    config.save(user, home / "config.json")
    print(f"mode set to {args.name}")
    return 0


def cmd_doctor(args) -> int:
    cfg, home = _load(args)
    print(f"jobhunt {__version__}; home {home}; mode {cfg['mode']}; tracker {cfg['tracker']}")
    issues = config.problems(cfg)
    if not (home / "profile.md").exists():
        issues.append("No profile yet. Run: python -m jobhunt init")
    try:
        import pymupdf  # noqa: F401
    except ImportError:
        issues.append("pymupdf isn't installed (needed for the resume check): pip install pymupdf")
    for m in issues:
        print(f"todo: {m}")
    if not issues:
        boards = sum(len(v) for v in cfg["companies"].values())
        feeds = [k for k, v in cfg["sources"].items() if v]
        print(f"ready: {len(cfg['titles']['include'])} title(s), {boards} company board(s), feeds: {', '.join(feeds) or 'none'}")
    return 1 if issues else 0


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="jobhunt", description="Job search engine that needs no AI calls.")
    p.add_argument("--version", action="version", version=__version__)
    p.add_argument("--home", help="private folder (default: ./private or $JOBHUNT_HOME)")
    sub = p.add_subparsers(dest="cmd", required=True)

    s = sub.add_parser("init", help="set up private/, your profile, config and tracker")
    s.add_argument("--resume", help="existing resume (.pdf, .tex, .md, .txt) to draft the profile from")
    s.add_argument("--name"), s.add_argument("--city")
    s.add_argument("--titles", help="comma-separated, e.g. \"product manager, senior product manager\"")
    s.add_argument("--exclude"), s.add_argument("--boost"), s.add_argument("--countries")
    s.add_argument("--priority", help="companies where you have a referral")
    s.add_argument("--companies", help="other companies to watch")
    s.add_argument("--pay-floor", dest="pay_floor", type=float)
    s.add_argument("--pay-target", dest="pay_target", type=float)
    s.add_argument("--tracker", choices=["csv", "sheet"]), s.add_argument("--sheet-id", dest="sheet_id")
    s.add_argument("--mode", choices=config.MODES)
    s.add_argument("--no-remote", action="store_true"), s.add_argument("--no-boards", action="store_true")
    s.add_argument("--force", action="store_true"), s.add_argument("--yes", action="store_true")
    s.set_defaults(fn=cmd_init)

    s = sub.add_parser("scan", help="find, filter and rank new jobs")
    s.add_argument("--sources", help="comma-separated subset, e.g. greenhouse,remoteok")
    s.add_argument("--limit", type=int), s.add_argument("--dry-run", action="store_true")
    s.add_argument("--include-seen", action="store_true", help="show jobs from earlier scans too")
    s.set_defaults(fn=cmd_scan)

    s = sub.add_parser("check", help="ATS pre-flight for a resume PDF")
    s.add_argument("pdf"), s.add_argument("--max-pages", type=int, default=1)
    s.add_argument("--jd", help="job description text file, for a keyword gap report")
    s.add_argument("--company", help="employer name, left out of the keyword report")
    s.add_argument("--letter", action="store_true", help="a cover letter: skip resume-only checks")
    s.set_defaults(fn=cmd_check)

    s = sub.add_parser("people", help="LinkedIn searches for a company")
    s.add_argument("company"), s.add_argument("title", nargs="?")
    s.add_argument("--peer", action="append", help="peer title to search (repeatable)")
    s.add_argument("--big", action="store_true", help="large company: narrow recruiters to tech")
    s.set_defaults(fn=cmd_people)

    s = sub.add_parser("boards", help="find and track company job boards")
    s.add_argument("action", choices=["add", "list"]), s.add_argument("names", nargs="*")
    s.set_defaults(fn=cmd_boards)

    s = sub.add_parser("sheet", help="print the requests that build the Google Sheet")
    s.add_argument("--rows", type=int, default=500)
    s.set_defaults(fn=cmd_sheet)

    s = sub.add_parser("applied", help="log an application (CSV tracker)")
    s.add_argument("company"), s.add_argument("role", nargs="?")
    s.add_argument("--channel", default="Cold application",
                   choices=["Referral", "Hiring manager message", "Cold application", "Auto-apply"])
    s.add_argument("--resume"), s.add_argument("--contacts"), s.add_argument("--notes")
    s.set_defaults(fn=cmd_applied)

    sub.add_parser("due", help="follow-ups due today (CSV tracker)").set_defaults(fn=cmd_due)
    sub.add_parser("stats", help="interviews by channel (CSV tracker)").set_defaults(fn=cmd_stats)
    s = sub.add_parser("mode", help="show or set how much the AI agents do")
    s.add_argument("name", nargs="?", choices=config.MODES)
    s.set_defaults(fn=cmd_mode)
    sub.add_parser("doctor", help="check the setup").set_defaults(fn=cmd_doctor)
    return p


def main(argv: list[str] | None = None) -> int:
    _utf8()
    args = build_parser().parse_args(argv)
    try:
        return args.fn(args)
    except FileNotFoundError as e:
        print(f"file not found: {e.filename or e}")
        return 2
    except ValueError as e:
        print(f"config problem: {e}")
        return 2
