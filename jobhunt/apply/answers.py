"""The answer bank: standing answers to the questions application forms repeat.

`private/answers.json` holds a list of entries. An entry matches a form question when
the question equals one of its `is` phrases, or contains every `ask` phrase and none of
its `not` phrases. The most specific match wins. An entry with a `country` is used only for
jobs in that country; `text` is the wording to use when the form gives a text box instead
of options. Nothing here guesses: a question with
no entry, or a choice question where no option fits the answer, is written to
`private/answers-pending.json` for the user to answer once.
"""
from __future__ import annotations

import datetime as dt
import json
import re
from pathlib import Path

from .. import config

COUNTRY_NAMES = {"US": "united states", "CA": "canada", "GB": "united kingdom"}
# A question that points at "the country this role is in" gets the job's country added,
# so one entry per country answers it.
_THIS_COUNTRY = re.compile(r"\b(country (this|the) (role|job|position)|country in which|country where|this country|"
                           r"in the country|location of (this|the) (role|job))")
YES = {"yes", "y", "true", "check", "checked", "agree"}
NO = {"no", "n", "false", "uncheck"}


def norm(text: str) -> str:
    """Lower-case, one line, no required-field star, country names spelled out."""
    t = re.sub(r"\s+", " ", (text or "").replace("’", "'")).strip()
    t = re.sub(r"[*✱]+", "", t)
    # "US", "U.S." and "USA" in capitals are the country; the lower-case word "us" is left alone
    t = re.sub(r"\bU\.?S\.?A?\b\.?", "united states", t)
    t = re.sub(r"\bU\.?K\b\.?", "united kingdom", t)
    t = t.lower().replace("united states of america", "united states")
    t = re.sub(r"\busa\b|\bu\.s\.a?\.?", "united states", t)
    return re.sub(r"\s+", " ", t).strip(" :")


def bank_path() -> Path:
    return config.home() / "answers.json"


def pending_path() -> Path:
    return config.home() / "answers-pending.json"


def load(path: Path | None = None) -> list[dict]:
    path = path or bank_path()
    if not path.exists():
        return []
    data = json.loads(path.read_text(encoding="utf-8"))
    return data["answers"] if isinstance(data, dict) else data


def save(entries: list[dict], path: Path | None = None) -> Path:
    path = path or bank_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps({"answers": entries}, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return path


def _question(label: str, country: str = "") -> str:
    q = norm(label)
    name = COUNTRY_NAMES.get((country or "").upper(), "")
    if name and name not in q and _THIS_COUNTRY.search(q):
        q += " " + name
    return q


def find(label: str, entries: list[dict], country: str = "") -> dict | None:
    """The most specific entry that matches this question, or None."""
    q = _question(label, country)
    best, best_score = None, -1
    for e in entries:
        if e.get("country") and e["country"].upper() != (country or "").upper():
            continue        # a per-country answer is used only when the job's country is known
        exact = [norm(p) for p in e.get("is", [])]
        asks = [norm(p) for p in e.get("ask", [])]
        if q in exact:
            score = 10_000 + len(q)
        elif asks and all(p in q for p in asks) and not any(norm(p) in q for p in e.get("not", [])):
            score = sum(len(p) for p in asks)
        else:
            continue
        if score > best_score:
            best, best_score = e, score
    return best


def choose(wanted, options: list[str]) -> list[str]:
    """Map an answer onto a form's options. `wanted` is one answer or a list of
    acceptable ones in order of preference. Returns [] when nothing fits."""
    wants = wanted if isinstance(wanted, list) else [wanted]
    lowered = [norm(o) for o in options]
    for w in wants:
        w = norm(str(w))
        if not w:
            continue
        tests = (lambda o: o == w,
                 lambda o: o.startswith(w + " ") or o.startswith(w + ","),
                 lambda o: o.startswith(w),
                 lambda o: re.search(r"\b" + re.escape(w) + r"\b", o) is not None)
        for test in tests:
            hits = [options[i] for i, o in enumerate(lowered) if test(o)]
            if len(hits) == 1:
                return hits
            if len(hits) > 1:      # "No" must not pick between two different "No, ..." options
                break
    return []


def choose_many(wanted, options: list[str]) -> list[str]:
    """For tick-all-that-apply questions: every wanted answer that has an option."""
    out = []
    for w in (wanted if isinstance(wanted, list) else [wanted]):
        for hit in choose(w, options):
            if hit not in out:
                out.append(hit)
    return out


def as_bool(value) -> bool | None:
    v = norm(str(value[0] if isinstance(value, list) and value else value))
    return True if v in YES else False if v in NO else None


def resolve(label: str, entries: list[dict], options: list[str] | None = None, country: str = "",
            many: bool = False):
    """Answer for one form question. Returns (value, entry). value is None when the bank has
    no answer that is safe to enter; otherwise a string for text or a list of option labels."""
    e = find(label, entries, country)
    if e is None:
        return None, None
    ans = e.get("answer")
    if ans in (None, "", []):
        return None, e
    if options:
        hits = choose_many(ans, options) if many else choose(ans, options)
        return (hits or None), e
    if e.get("text"):               # a fuller answer for when the form gives a text box
        return str(e["text"]), e
    return (str(ans[0]) if isinstance(ans, list) else str(ans)), e


# ---- questions waiting for the user ----------------------------------------------------

def load_pending() -> list[dict]:
    p = pending_path()
    return json.loads(p.read_text(encoding="utf-8")) if p.exists() else []


def save_pending(items: list[dict]) -> None:
    pending_path().parent.mkdir(parents=True, exist_ok=True)
    pending_path().write_text(json.dumps(items, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def add_pending(label: str, options: list[str] | None, company: str, url: str, why: str = "") -> None:
    items = load_pending()
    q = norm(label)
    for it in items:
        if norm(it["question"]) == q and sorted(it.get("options") or []) == sorted(options or []):
            if company and company not in it["companies"]:
                it["companies"].append(company)
            break
    else:
        items.append({"question": re.sub(r"\s+", " ", label).strip(), "options": options or [],
                      "companies": [company] if company else [], "url": url, "why": why,
                      "asked": dt.date.today().isoformat()})
    save_pending(items)


def answer_pending(index: int, answer: str) -> dict:
    """Move pending question number `index` (1-based) into the bank with this answer."""
    items = load_pending()
    it = items.pop(index - 1)
    entry = {"is": [norm(it["question"])], "answer": answer, "added": dt.date.today().isoformat()}
    entries = load()
    entries.append(entry)
    save(entries)
    save_pending(items)
    return entry
