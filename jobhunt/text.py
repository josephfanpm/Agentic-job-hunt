"""Small text helpers: HTML stripping, matching, pay and date parsing."""
from __future__ import annotations

import datetime as dt
import html
import re
import unicodedata
from email.utils import parsedate_to_datetime

_BREAK = re.compile(r"<\s*(br|/p|/li|/div|/h\d|/tr)[^>]*>", re.I)
_TAG = re.compile(r"<[^>]+>")
_SPACE = re.compile(r"[ \t\r\f\v]+")


def strip_html(s: str | None) -> str:
    """HTML (possibly entity-escaped, as Greenhouse sends it) to plain text."""
    if not s:
        return ""
    s = html.unescape(s)
    s = _BREAK.sub("\n", s)
    s = _TAG.sub(" ", s)
    s = html.unescape(s)
    s = _SPACE.sub(" ", s)
    return re.sub(r" *\n\s*", "\n", s).strip()


def norm(s: str | None) -> str:
    """Lowercase, strip accents and punctuation, collapse spaces."""
    if not s:
        return ""
    s = unicodedata.normalize("NFKD", s)
    s = "".join(ch for ch in s if not unicodedata.combining(ch)).lower()
    return re.sub(r"[^a-z0-9+#]+", " ", s).strip()


_TITLE_ALIASES = [(r"\bsr\b", "senior"), (r"\bjr\b", "junior"), (r"\bmgr\b", "manager"),
                  (r"\bmgmt\b", "management"), (r"\beng\b", "engineer")]


def norm_title(s: str | None) -> str:
    t = norm(s)
    for pat, rep in _TITLE_ALIASES:
        t = re.sub(pat, rep, t)
    return t


def has_phrase(haystack_norm: str, phrase: str) -> bool:
    """Whole-word phrase match on already-normalized text."""
    p = norm_title(phrase)
    return bool(p) and f" {p} " in f" {haystack_norm} "


# Lines about perks and legal notices mention "health", "growth" and the like
# without saying anything about the work, so matching leaves them out.
_BOILERPLATE = ("insurance", "401", "dental", "paid time off", "pto", "parental leave", "wellness",
                "stipend", "equal opportunity", "accommodation", "benefits", "vacation",
                "disability", "veteran", "retirement", "reimbursement", "perks", "paid sick",
                "bias audit", "applicants", "pursuant", "ordinance", "fair chance", "e-verify",
                "background check", "protected by", "criminal histor", "sexual orientation",
                "base salary", "compensation range", "pay range", "salary range",
                "recruitment tool", "decision-making", "notice regarding", "privacy")


def drop_boilerplate(text: str) -> str:
    """The text minus benefits, pay-disclosure and legal lines."""
    keep = []
    for part in re.split(r"(?<=[.;•])\s+|\n", text):
        low = part.lower()
        if not any(marker in low for marker in _BOILERPLATE):
            keep.append(part)
    return "\n".join(keep)


# ---- pay -------------------------------------------------------------------
_CUR = r"(?:CA\$|C\$|CAD\s?\$?|US\$|USD\s?\$?|\$|£|€)"
_NUM = r"(?:\d{1,3}(?:,\d{3})+(?:\.\d+)?|\d{2,3}(?:\.\d)?\s?[kK]\b)"
_PAY = re.compile(rf"(?P<cur>{_CUR})\s?(?P<a>{_NUM})\s*(?:-|–|—|to)\s*(?:{_CUR})?\s?(?P<b>{_NUM})")


def _amount(s: str) -> float:
    s = s.strip().replace(",", "")
    if s[-1] in "kK":
        return float(s[:-1].strip()) * 1000
    return float(s)


def _cur_label(c: str) -> str:
    c = c.strip().upper().replace(" ", "")
    if c.startswith(("CA", "C$")):
        return "CAD "
    if c.startswith("US"):
        return "USD "
    return c  # "$", "£", "€" stay as written; a bare "$" is not assumed to be USD


def parse_pay(text: str) -> tuple[str, float | None, float | None]:
    """Find yearly pay ranges written in the posting. Returns (display, min, max).

    Postings often list one range per location, so this reports the lowest
    minimum and the highest maximum. Nothing found means ("", None, None):
    pay is never estimated.
    """
    lo = hi = None
    label = ""
    for m in list(_PAY.finditer(text))[:6]:
        try:
            a, b = _amount(m["a"]), _amount(m["b"])
        except ValueError:
            continue
        if not (20_000 <= a <= b <= 2_000_000):
            continue  # hourly rates, bonuses, headcounts and the like
        label = label or _cur_label(m["cur"])
        lo = a if lo is None else min(lo, a)
        hi = b if hi is None else max(hi, b)
    if lo is None:
        return "", None, None
    return f"{label}{lo:,.0f}–{hi:,.0f}", lo, hi


# ---- dates -----------------------------------------------------------------
def to_date(value) -> str:
    """Best-effort conversion of the feeds' date formats to yyyy-mm-dd."""
    if value in (None, ""):
        return ""
    if isinstance(value, (int, float)) or (isinstance(value, str) and value.strip().isdigit()):
        n = float(value)
        if n > 1e11:  # milliseconds
            n /= 1000
        try:
            return dt.datetime.fromtimestamp(n, dt.timezone.utc).date().isoformat()
        except (OverflowError, OSError, ValueError):
            return ""
    s = str(value).strip()
    try:
        return dt.datetime.fromisoformat(s.replace("Z", "+00:00")).date().isoformat()
    except ValueError:
        pass
    for fmt in ("%B %d, %Y", "%b %d, %Y", "%Y/%m/%d", "%m/%d/%Y"):
        try:
            return dt.datetime.strptime(s, fmt).date().isoformat()
        except ValueError:
            pass
    try:
        return parsedate_to_datetime(s).date().isoformat()
    except (TypeError, ValueError):
        return ""


def days_ago(date_str: str, today: dt.date | None = None) -> int | None:
    if not date_str:
        return None
    today = today or dt.date.today()
    try:
        return (today - dt.date.fromisoformat(date_str)).days
    except ValueError:
        return None
