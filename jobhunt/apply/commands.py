"""Command-line entry points: apply, answers, signin, mailcode."""
from __future__ import annotations

import json
import os
import shutil
import time
from pathlib import Path

from .. import config
from . import answers as bank
from . import mailcode
from .browser import need_playwright


def _home(args) -> None:
    if getattr(args, "home", None):
        os.environ["JOBHUNT_HOME"] = str(Path(args.home).resolve())


def cmd_apply(args) -> int:
    _home(args)
    miss = need_playwright()
    if miss:
        print(miss)
        return 2
    if not bank.load():
        print("No answer bank yet. Run: python -m jobhunt answers init   then fill in private/answers.json")
        return 2
    for label, f in (("resume", args.resume), ("cover letter", args.cover)):
        if f and not Path(f).exists():
            print(f"{label} not found: {f}")
            return 2
    if not args.resume:
        print("Give the resume to upload: --resume path/to/First_Last_Resume_Company.pdf")
        return 2
    from . import run
    res = run.apply(args.url, args.company, role=args.role or "", resume=str(Path(args.resume).resolve()),
                    cover=str(Path(args.cover).resolve()) if args.cover else "", country=(args.country or "").upper(),
                    submit=not args.dry_run)
    print(f"{res['status'].upper()}: {res['company']}" + (f", {res['role']}" if res["role"] else "") + f"  ({res.get('detail', '')})")
    for q, a in res.get("entered", []):
        print(f"  - {q[:70]} => {str(a)[:90]}")
    for q, opts, why in res.get("pending", []):
        print(f"  ? {q[:110]}" + (f"  [{', '.join(opts[:6])}]" if opts else "") + (f"  ({why})" if why else ""))
    for b in res.get("blockers", []):
        print(f"  ! {b}")
    if res.get("pending"):
        print("Answer them once with: python -m jobhunt answers   (essays go in the job's answers.json), then run this again.")
    print(f"Record: {res['folder']}")
    return 0 if res["status"] in ("submitted", "ready") else 1


def cmd_answers(args) -> int:
    _home(args)
    if args.action == "init":
        if bank.bank_path().exists():
            print(f"{bank.bank_path()} already exists; edit it directly.")
            return 0
        shutil.copy(config.ROOT / "examples" / "answers.example.json", bank.bank_path())
        print(f"Created {bank.bank_path()}. Replace every placeholder with your own answer; delete entries you'd rather be asked about.")
        return 0
    if args.action == "list":
        for e in bank.load():
            print(f"{' + '.join(e.get('is') or e.get('ask') or [])}" + (f"  [{e['country']}]" if e.get("country") else "")
                  + f"  =>  {e.get('answer')}")
        return 0
    if args.action == "add":
        if len(args.rest) < 2:
            print('usage: python -m jobhunt answers add "words from the question" "your answer" [--country US]')
            return 2
        entry = {"ask": [p.strip() for p in args.rest[0].split("+")], "answer": args.rest[1]}
        if args.country:
            entry["country"] = args.country.upper()
        entries = bank.load()
        entries.append(entry)
        bank.save(entries)
        print(f"saved: {entry['ask']} => {entry['answer']}")
        return 0
    pending = bank.load_pending()
    if args.action == "set":
        if len(args.rest) < 2 or not args.rest[0].isdigit() or not 1 <= int(args.rest[0]) <= len(pending):
            print('usage: python -m jobhunt answers set <number> "your answer"')
            return 2
        entry = bank.answer_pending(int(args.rest[0]), args.rest[1])
        print(f"saved: {entry['is'][0]} => {entry['answer']}")
        return 0
    if args.action == "skip":
        if not args.rest or not args.rest[0].isdigit() or not 1 <= int(args.rest[0]) <= len(pending):
            print("usage: python -m jobhunt answers skip <number>")
            return 2
        pending.pop(int(args.rest[0]) - 1)
        bank.save_pending(pending)
        return 0
    if not pending:
        print("No questions are waiting. Forms ask from private/answers.json; see it with: python -m jobhunt answers list")
        return 0
    print("Questions forms asked that have no saved answer:\n")
    for i, it in enumerate(pending, 1):
        print(f"{i}. {it['question']}  ({', '.join(it['companies'])})")
        if it.get("options"):
            print("     options: " + " | ".join(it["options"][:12]))
        if it.get("why"):
            print(f"     note: {it['why']}")
    print('\nAnswer one for every future form:  python -m jobhunt answers set <number> "your answer"')
    print("For a choice question, give the option's text, or its first words.")
    print("An essay that only fits one job goes in that job's folder instead: private/applications/<Company>/answers.json")
    return 0


def cmd_signin(args) -> int:
    _home(args)
    miss = need_playwright()
    if miss:
        print(miss)
        return 2
    from . import run
    if not run.sign_in(args.url):
        print("Chrome was not found. Install Google Chrome, or sign in during the apply run itself.")
        return 1
    print("Sign in in the Chrome window that opened, and leave that window open: later runs use it, already signed in.")
    return 0


def cmd_mailcode(args) -> int:
    _home(args)
    cfg = config.load()
    why = mailcode.ready(cfg)
    if why:
        print(f"The email code reader is not set up: {why}.")
        print('In private/config.json:  "email_codes": {"enabled": true, "user": "you@gmail.com"}')
        print("Then create an app password for that mailbox (Gmail: myaccount.google.com/apppasswords, needs 2-step "
              "verification) and save it in private/email-password.txt, or set JOBHUNT_EMAIL_PASSWORD.")
        return 1
    try:
        box = mailcode.connect(cfg)
    except Exception as exc:
        print(f"Could not sign in to the mailbox: {exc}")
        return 1
    msgs = mailcode.recent(box, time.time() - 86400)
    box.logout()
    print(f"Signed in to {cfg['email_codes']['user']} (read-only). Code emails in the last day: {len(msgs)}")
    for m in msgs[:5]:
        code = mailcode.extract_code(m["subject"] + "\n" + m["text"])
        print(f"  - {m['subject'][:70]}  => code {'found' if code else 'not found'}")
    return 0


def register(sub) -> None:
    s = sub.add_parser("apply", help="fill and submit one application in your browser")
    s.add_argument("url")
    s.add_argument("--company", required=True)
    s.add_argument("--role", default="")
    s.add_argument("--resume", help="the PDF to upload")
    s.add_argument("--cover", help="cover letter PDF, uploaded where the form takes one")
    s.add_argument("--country", help="the job's country (US, CA...), for work-authorization questions")
    s.add_argument("--dry-run", action="store_true", help="fill the form and save the record, but don't submit")
    s.set_defaults(fn=cmd_apply)
    s = sub.add_parser("answers", help="your saved answers to common form questions")
    s.add_argument("action", nargs="?", default="pending", choices=["pending", "list", "init", "set", "add", "skip"])
    s.add_argument("rest", nargs="*")
    s.add_argument("--country")
    s.set_defaults(fn=cmd_answers)
    s = sub.add_parser("signin", help="open a careers site in the kept browser so you can sign in once")
    s.add_argument("url")
    s.set_defaults(fn=cmd_signin)
    sub.add_parser("mailcode", help="check the reader for emailed security codes").set_defaults(fn=cmd_mailcode)
