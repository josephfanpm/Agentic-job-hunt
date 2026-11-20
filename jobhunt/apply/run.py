"""Run one application from start to finish: open the form, fill it, keep a record,
submit, enter an emailed code, wait for the user at a captcha or sign-in, and confirm."""
from __future__ import annotations

import datetime as dt
import json
import re
import time
from pathlib import Path

from .. import config
from . import answers as bank
from . import forms, human, mailcode
from .browser import open_browser

CONFIRM_TEXT = ("application has been submitted", "application was successfully submitted", "application submitted",
                "thank you for applying", "thanks for applying", "we've received your application",
                "we have received your application", "your application has been received", "successfully submitted")
CODE_TEXT = ("verification code was sent", "security code", "enter the code", "code we sent", "code we emailed")
SUBMIT_NAMES = ("Submit application", "Submit Application", "Submit", "Send application", "Apply")
NEXT_NAMES = ("Next", "Continue", "Save and continue", "Save & continue", "Save and Continue", "Review")

SITES = {
    "greenhouse": {"match": r"greenhouse\.io", "confirm_url": "confirmation"},
    "ashby": {"match": r"ashbyhq\.com", "suffix": "/application"},
    "lever": {"match": r"jobs\.(eu\.)?lever\.co", "suffix": "/apply", "confirm_url": "/thanks",
              "extra_combo": "input[name=location]"},
    "amazon": {"match": r"amazon\.jobs", "steps": True, "apply_link": "a#apply-button, a:has-text('Apply now')",
               "signin_url": r"passport\.amazon\.jobs|/account/|signin"},
    "other": {"match": r".", "steps": True},
}


def site_for(url: str) -> tuple[str, dict]:
    for name, s in SITES.items():
        if re.search(s["match"], url):
            return name, s
    return "other", SITES["other"]


def form_url(url: str, site: dict) -> str:
    suffix = site.get("suffix")
    if suffix and not url.split("?")[0].rstrip("/").endswith(suffix):
        base, _, query = url.partition("?")
        return base.rstrip("/") + suffix + ("?" + query if query else "")
    return url


def safe_name(text: str) -> str:
    return re.sub(r"[^A-Za-z0-9]+", "_", text).strip("_")[:60] or "job"


def app_dir(company: str, role: str = "") -> Path:
    d = config.home() / "applications" / (safe_name(company) + ("__" + safe_name(role) if role else ""))
    d.mkdir(parents=True, exist_ok=True)
    return d


def write_record(folder: Path, company: str, role: str, url: str, rep: forms.Report, status: str) -> Path:
    lines = [f"# {company}" + (f": {role}" if role else ""), url, f"{dt.date.today().isoformat()}: {status}", "",
             "| Question | Answer entered |", "|---|---|"]
    lines += [f"| {q.replace('|', '/')} | {str(a).replace('|', '/').replace(chr(10), ' ')} |" for q, a in rep.entered]
    if rep.pending:
        lines += ["", "## Not answered (the form was not submitted)"]
        lines += [f"- {q}" + (f"  (options: {', '.join(o[:8])})" if o else "") + (f"  [{why}]" if why else "")
                  for q, o, why in rep.pending]
    if rep.blockers:
        lines += ["", "## Needs you"] + [f"- {b}" for b in rep.blockers]
    path = folder / "answers.md"
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return path


def _button(page, names):
    for n in names:
        b = page.get_by_role("button", name=n, exact=True)
        for i in range(b.count()):
            if b.nth(i).is_visible() and b.nth(i).is_enabled():
                return b.nth(i)
    return None


def _confirmed(page, site: dict) -> bool:
    if site.get("confirm_url") and site["confirm_url"] in page.url:
        return True
    body = (page.inner_text("body", timeout=3000) or "").lower()
    return any(t in body for t in CONFIRM_TEXT)


def _code_wanted(page):
    """The boxes a site shows for an emailed code, or None."""
    boxes = page.locator('input[id^="security-input"], input[name*="security_code"], input[autocomplete="one-time-code"]')
    if boxes.count() and boxes.first.is_visible():
        return boxes
    return None


def _errors(page) -> list[str]:
    try:
        found = page.locator('[class*="error"]:visible, [role="alert"]:visible').all_inner_texts()
    except Exception:
        return []
    out = []
    for t in found:
        t = re.sub(r"\s+", " ", t).strip()
        if t and t not in out and len(t) < 300:
            out.append(t)
    return out[:8]


def _pace(cfg: dict) -> None:
    """Leave a gap between submissions; a person doesn't send five forms in a minute."""
    gap = int(cfg["auto_apply"].get("minutes_between", 2)) * 60
    stamp = config.home() / "cache" / "last-apply.txt"
    if stamp.exists():
        wait = gap - (time.time() - float(stamp.read_text() or 0))
        if 0 < wait <= gap:
            print(f"waiting {int(wait)}s before submitting (auto_apply.minutes_between)", flush=True)
            time.sleep(wait)
    stamp.parent.mkdir(parents=True, exist_ok=True)
    stamp.write_text(str(time.time()))


def _fill_all(page, ctx: forms.Context, rep: forms.Report) -> forms.Report:
    for _ in range(4):                    # answers can reveal follow-up questions
        before = len(rep.done)
        forms.fill(page, ctx, rep)
        if len(rep.done) == before:
            break
        page.wait_for_timeout(700)
    return rep


def _after_submit(page, cfg: dict, site: dict, company: str, wait: int) -> tuple[str, str]:
    """Watch the page after Submit. Returns (status, detail)."""
    sent_at = time.time() - 30
    end = time.time() + wait
    code_tried = told_captcha = False
    quiet_since = time.time()
    while time.time() < end:
        page.wait_for_timeout(1500)
        try:
            if _confirmed(page, site):
                return "submitted", page.url
            boxes = _code_wanted(page)
            if boxes is not None and not code_tried:
                code_tried = True
                why = mailcode.ready(cfg)
                if why:
                    human.notify("Job application needs you", f"{company}: type the code from your email into the form ({why}).")
                else:
                    print("the site emailed a security code; reading it from the inbox", flush=True)
                    code = mailcode.wait_for_code(cfg, sent_at, hints=(company, "greenhouse"), timeout=180)
                    if code:
                        boxes.first.click()
                        page.keyboard.type(code, delay=60)
                        page.wait_for_timeout(600)
                        b = _button(page, SUBMIT_NAMES)
                        if b:
                            b.click()
                    else:
                        human.notify("Job application needs you", f"{company}: no code email arrived; type it into the form.")
                quiet_since = time.time()
                continue
            if human.captcha_showing(page):
                if not told_captcha:
                    told_captcha = True
                    human.notify("Job application needs you", f"{company}: answer the 'are you human' check in the browser window. "
                                                              "Everything else is filled in.")
                    try:
                        page.bring_to_front()
                    except Exception:
                        pass
                quiet_since = time.time()
                continue
            if boxes is None and not told_captcha and time.time() - quiet_since > 25:
                errs = _errors(page)
                if errs:
                    return "error", "; ".join(errs)
        except Exception:
            pass
    if told_captcha:
        return "waiting", "the human check was not answered in time; the form was not sent"
    if code_tried:
        return "waiting", "the emailed code was not entered in time; the form was not sent"
    return "unconfirmed", "no confirmation page appeared: check your email before trying again"


def apply(url: str, company: str, role: str = "", resume: str = "", cover: str = "", country: str = "",
          submit: bool = True, job_answers: dict | None = None, cfg: dict | None = None, wait: int | None = None) -> dict:
    """Fill one application and, unless `submit` is False, send it. Returns a result dict
    with status: submitted, ready (dry run), waiting (needs the user), error or unconfirmed."""
    from playwright.sync_api import sync_playwright

    cfg = cfg or config.load()
    name, site = site_for(url)
    folder = app_dir(company, role)
    saved = folder / "answers.json"
    if job_answers is None and saved.exists():
        job_answers = json.loads(saved.read_text(encoding="utf-8"))
    ctx = forms.Context(entries=bank.load(), job=forms.job_entries(job_answers or {}), resume=resume, cover=cover,
                        country=country, company=company, url=url, extra_combo=site.get("extra_combo", ""))
    wait = wait or int(cfg["auto_apply"].get("wait_for_user_minutes", 15)) * 60
    result = {"company": company, "role": role, "url": url, "site": name, "folder": str(folder)}
    with sync_playwright() as p:
        ctxb = open_browser(p, cfg)
        page = ctxb.pages[0] if ctxb.pages else ctxb.new_page()
        try:
            page.goto(form_url(url, site), wait_until="domcontentloaded", timeout=90000)
            page.wait_for_timeout(4000)
            if site.get("apply_link"):
                link = page.locator(site["apply_link"]).first
                if link.count():
                    link.click()
                    page.wait_for_timeout(5000)
            if site.get("signin_url") and re.search(site["signin_url"], page.url):
                ok = human.wait_for_user(page, f"{company}: sign in to the careers site in the browser window. "
                                         "It stays signed in for next time.",
                                         lambda pg: not re.search(site["signin_url"], pg.url), timeout=wait)
                if not ok:
                    result.update(status="waiting", detail="sign-in was not completed")
                    return result
                page.wait_for_timeout(4000)
            rep = forms.Report()
            for step in range(12 if site.get("steps") else 1):
                rep_before = len(rep.done)
                forms.fill(page, ctx, rep, only_files=True)       # resume first: some sites read it and fill fields
                if len(rep.done) > rep_before:
                    page.wait_for_timeout(6000 if name == "ashby" else 2500)
                _fill_all(page, ctx, rep)
                if not rep.ok or _button(page, SUBMIT_NAMES[:4]) or not site.get("steps"):
                    break
                nxt = _button(page, NEXT_NAMES)
                if not nxt:
                    if len(rep.done) == rep_before:
                        rep.blockers.append("Could not find the form's Submit or Next button on this page.")
                    break
                page.screenshot(path=str(folder / f"step-{step + 1}.png"), full_page=True)
                nxt.click()
                page.wait_for_timeout(4000)
            for q, opts, why in rep.pending:
                bank.add_pending(q, opts, company, url, why)
            page.wait_for_timeout(600)
            try:
                page.screenshot(path=str(folder / "form.png"), full_page=True)
            except Exception:
                pass
            if not rep.ok:
                status = "waiting"
                detail = f"{len(rep.pending)} question(s) with no saved answer, {len(rep.blockers)} item(s) for you"
            elif not submit:
                status, detail = "ready", "filled, not submitted (dry run)"
            else:
                write_record(folder, company, role, url, rep, "submitting")
                _pace(cfg)
                btn = _button(page, SUBMIT_NAMES)
                if not btn:
                    status, detail = "waiting", "no Submit button found"
                else:
                    btn.click()
                    status, detail = _after_submit(page, cfg, site, company, wait)
                    try:
                        page.screenshot(path=str(folder / "after.png"), full_page=True)
                    except Exception:
                        pass
            write_record(folder, company, role, url, rep, f"{status}: {detail}")
            result.update(status=status, detail=detail, entered=rep.entered,
                          pending=[(q, o, w) for q, o, w in rep.pending], blockers=rep.blockers)
            return result
        finally:
            ctxb.close()


def sign_in(url: str, cfg: dict | None = None, minutes: int = 15) -> None:
    """Open a site in the kept browser profile so the user can sign in once."""
    from playwright.sync_api import sync_playwright

    cfg = cfg or config.load()
    with sync_playwright() as p:
        ctxb = open_browser(p, cfg)
        page = ctxb.pages[0] if ctxb.pages else ctxb.new_page()
        page.goto(url, wait_until="domcontentloaded", timeout=90000)
        print(f"Sign in in the browser window, then close it. It closes by itself after {minutes} minutes.", flush=True)
        end = time.time() + minutes * 60
        try:
            while time.time() < end and ctxb.pages:
                ctxb.pages[0].wait_for_timeout(1500)
        except Exception:
            pass
        try:
            ctxb.close()
        except Exception:
            pass
