"""Read the security code a job site emails during an application.

Greenhouse and some other sites email a short code and wait for it before they accept
the form. This reads the user's own inbox over IMAP, read-only, and returns the code.

Setup (once): turn on IMAP for the mailbox, create an app password, and put it in the
JOBHUNT_EMAIL_PASSWORD environment variable or in `private/email-password.txt`.
Config: "email_codes": {"enabled": true, "user": "you@example.com", "host": "imap.gmail.com"}
"""
from __future__ import annotations

import email
import email.utils
import html
import imaplib
import os
import re
import time
from email.header import decode_header, make_header

from .. import config

SUBJECT_HINTS = ("security code", "verification code", "verify your", "one-time", "passcode", "confirm your email")


def _text(msg) -> str:
    parts = []
    for part in (msg.walk() if msg.is_multipart() else [msg]):
        if part.get_content_type() not in ("text/plain", "text/html"):
            continue
        raw = part.get_payload(decode=True) or b""
        body = raw.decode(part.get_content_charset() or "utf-8", errors="replace")
        if part.get_content_type() == "text/html":
            body = html_to_text(body)
        parts.append(body)
    return "\n".join(parts)


def html_to_text(body: str) -> str:
    body = re.sub(r"(?is)<(style|script).*?</\1>", " ", body)
    body = re.sub(r"(?i)<br\s*/?>|</(p|div|tr|h\d|td|li)>", "\n", body)
    return html.unescape(re.sub(r"<[^>]+>", " ", body))


def _looks_like_code(tok: str) -> bool:
    """A digit, or letters in mixed case, so an ordinary word like "Thanks" never counts."""
    if re.search(r"\d", tok):
        return True
    return tok not in (tok.lower(), tok.upper(), tok.capitalize())


def extract_code(text: str) -> str | None:
    """Pull the code out of an email body. Returns None unless one candidate is clear."""
    lines = [re.sub(r"\s+", " ", ln).strip() for ln in text.splitlines()]
    lines = [ln for ln in lines if ln]
    flat = " \n ".join(lines)
    # "...code...: aB3dE9fG" or "your code is 123456"
    for m in re.finditer(r"(?i)\bcode\b[^\n:]{0,80}(?::| is)\s*\n?\s*([A-Za-z0-9]{4,10})\b(?!@|\.\w)", flat):
        if _looks_like_code(m.group(1)):
            return m.group(1)
    alone = {ln for ln in lines if re.fullmatch(r"[A-Za-z0-9]{4,10}", ln) and _looks_like_code(ln)}
    if len(alone) == 1:
        return alone.pop()
    digits = set(re.findall(r"(?<![\d$.,#-])\b\d{6}\b(?![\d.,%-])", flat))
    return digits.pop() if len(digits) == 1 else None


def password() -> str:
    pw = os.environ.get("JOBHUNT_EMAIL_PASSWORD", "")
    f = config.home() / "email-password.txt"
    if not pw and f.exists():
        pw = f.read_text(encoding="utf-8").strip()
    return pw.replace(" ", "")


def ready(cfg: dict) -> str:
    """Empty string when the reader can run, else what is missing, in plain words."""
    ec = cfg.get("email_codes", {})
    if not ec.get("enabled"):
        return "email_codes.enabled is off"
    if not ec.get("user"):
        return "email_codes.user is empty"
    if not password():
        return "no app password (JOBHUNT_EMAIL_PASSWORD or private/email-password.txt)"
    return ""


def connect(cfg: dict) -> imaplib.IMAP4_SSL:
    ec = cfg["email_codes"]
    box = imaplib.IMAP4_SSL(ec.get("host") or "imap.gmail.com")
    box.login(ec["user"], password())
    box.select(ec.get("folder") or "INBOX", readonly=True)   # read-only: nothing is marked read or moved
    return box


def recent(box, since: float, hints: tuple = ()) -> list[dict]:
    """Code emails that arrived after `since` (epoch seconds), newest first."""
    day = time.strftime("%d-%b-%Y", time.gmtime(since - 86400))
    _, data = box.search(None, "SINCE", day)
    out = []
    for num in reversed(data[0].split()[-25:]):
        _, raw = box.fetch(num, "(BODY.PEEK[])")
        msg = email.message_from_bytes(raw[0][1])
        try:
            when = email.utils.parsedate_to_datetime(msg["Date"]).timestamp()
        except Exception:
            when = 0
        if when < since - 60:
            continue
        subject = str(make_header(decode_header(msg["Subject"] or "")))
        sender = str(make_header(decode_header(msg["From"] or "")))
        hay = (subject + " " + sender).lower()
        if not any(h in hay for h in SUBJECT_HINTS) and not any(h.lower() in hay for h in hints if h):
            continue
        out.append({"when": when, "subject": subject, "from": sender, "text": _text(msg)})
    return sorted(out, key=lambda m: -m["when"])


def wait_for_code(cfg: dict, since: float, hints: tuple = (), timeout: int = 180, poll: int = 6) -> str | None:
    """Wait for a code email that arrived after `since`. `hints` are words expected in the
    subject or sender (the company or site name); a message matching one is tried first."""
    box = connect(cfg)
    try:
        end = time.time() + timeout
        while time.time() < end:
            box.noop()
            msgs = recent(box, since, hints)
            msgs.sort(key=lambda m: (not any(h and h.lower() in (m["subject"] + m["from"]).lower() for h in hints),
                                     -m["when"]))
            for m in msgs:
                code = extract_code(m["subject"] + "\n" + m["text"])
                if code:
                    return code
            time.sleep(poll)
        return None
    finally:
        try:
            box.logout()
        except Exception:
            pass
