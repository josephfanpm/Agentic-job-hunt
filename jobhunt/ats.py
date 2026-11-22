"""ATS pre-flight: read a resume PDF the way an applicant tracking system does.

An ATS doesn't see your layout. It pulls the text out of the PDF in stored
order and looks for contact details, section headings, dates and keywords.
This check does the same and reports what a parser would trip on. It also
reads each bullet the way a recruiter skims it: does it carry a number, does
it open with an action, and is every listed tool shown in a bullet.

FAIL = fix before sending. WARN = look at it. Requires: pip install pymupdf
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path

LIGATURES = {chr(c) for c in range(0xFB00, 0xFB07)}
_EMAIL = re.compile(r"[\w.+-]+@[\w-]+\.[\w.-]+")
_PHONE = re.compile(r"(?:\+?\d{1,3}[\s.-]?)?\(?\d{3}\)?[\s.-]?\d{3}[\s.-]?\d{4}")
_MONTH = r"(?:jan|feb|mar|apr|may|jun|jul|aug|sep|sept|oct|nov|dec)[a-z]*\.?"
_DATE_RANGE = re.compile(
    rf"(?:{_MONTH}\s+)?(?:19|20)\d{{2}}(?:\s*[^\w\s]{{1,3}}\s*|\s+to\s+)(?:(?:{_MONTH}\s+)?(?:19|20)\d{{2}}|present|current|now)",
    re.I)
_SECTIONS = {
    "experience": ["experience", "work experience", "professional experience", "employment",
                   "employment history", "work history", "relevant experience"],
    "education": ["education", "education and training", "academic background"],
}

BULLET_CHARS = "•◦▪▸►●○■–-*·"
# Openers that describe a duty instead of an action and its result.
WEAK_OPENERS = ("responsible for", "helped", "helping", "assisted", "worked on", "participated in",
                "involved in", "tasked with", "duties included", "in charge of")
# Filler that tells a recruiter nothing they can check.
FILLER = ("team player", "various", "hard-working", "hardworking", "detail-oriented", "self-starter",
          "go-getter", "results-driven", "results-oriented", "think outside the box", "synergy",
          "proven track record", "fast-paced environment")
_NUMBER_WORDS = re.compile(r"\b(?:two|three|four|five|six|seven|eight|nine|ten|eleven|twelve|twenty|"
                           r"dozens?|hundreds?|thousands?|millions?|billions?|doubled|tripled|halved)\b", re.I)
_YEAR = re.compile(r"\b(?:19|20)\d{2}\b")
# Lines that list tools. Languages, Licensure and Interests aren't tools to demonstrate.
_TOOL_LINE = re.compile(r"^\s*(?:tools|skills|technical skills|software skills|software|technologies|"
                        r"frameworks|tech stack)\s*:\s*(.+)$", re.I)
METRIC_TARGET = 0.8


@dataclass
class Report:
    path: str
    pages: int = 0
    fails: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    info: list[str] = field(default_factory=list)
    keywords: dict | None = None

    @property
    def ok(self) -> bool:
        return not self.fails


def _lines(page) -> list[dict]:
    """Visual lines in stored order, with geometry and font, bullets removed."""
    rows, marks = [], []
    for block in page.get_text("dict")["blocks"]:
        for ln in block.get("lines", []):
            first = next((sp["text"].strip() for sp in ln["spans"] if sp["text"].strip()), "")
            spans = [sp for sp in ln["spans"] if sp["text"].strip()
                     and any(ch.isalnum() for ch in sp["text"])]
            if not spans:
                if first and first in BULLET_CHARS:
                    marks.append(ln["bbox"])   # a bullet glyph stored as its own line
                continue
            rows.append({
                "bullet": first[:1] in BULLET_CHARS and (len(first) == 1 or first[1] == " "),
                "x0": spans[0]["bbox"][0], "x1": ln["bbox"][2], "y0": ln["bbox"][1], "y1": ln["bbox"][3],
                "text": " ".join(sp["text"].strip() for sp in spans),
                "size": round(spans[0]["size"], 1), "bold": bool(spans[0]["flags"] & 16),
            })
    for _, my0, mx1, my1 in marks:
        for r in rows:
            if my0 < r["y1"] and my1 > r["y0"] and r["x0"] - 30 < mx1 <= r["x0"] + 2:
                r["bullet"] = True
                break
    return rows


def text_fails(text: str, pno: int = 1) -> list[str]:
    """Characters in the extracted text that an ATS can't read as words."""
    out = []
    found = sorted({ch for ch in text if ch in LIGATURES})
    if found:
        out.append(f"page {pno}: fused letters {found}. An ATS reads 'staffing' as 'sta?ing'. "
                   "In LaTeX, load fontspec with Ligatures=NoCommon")
    bad = sum(1 for ch in text if ch == "�" or 0xE000 <= ord(ch) <= 0xF8FF)
    if bad > 3:
        out.append(f"page {pno}: {bad} unreadable characters; the font has no text mapping")
    return out


def bullets(rows: list[dict]) -> list[str]:
    """Join each bulleted line with the lines that wrap under it."""
    out: list[str] = []
    cur: dict | None = None
    for r in rows:
        if r["bullet"]:
            cur = dict(r)
            out.append(r["text"].lstrip(BULLET_CHARS + " "))
        elif (cur and not r["bold"] and r["size"] == cur["size"] and cur["x0"] - 4 < r["x0"] < cur["x0"] + 16
              and 0 < r["y0"] - cur["y0"] < 2.2 * r["size"]):
            out[-1] += " " + r["text"]
            cur["y0"] = r["y0"]
        else:
            cur = None
    return out


def has_number(text: str) -> bool:
    """A measured result: a digit that isn't only a year, or a number word."""
    return bool(re.search(r"\d", _YEAR.sub("", text)) or _NUMBER_WORDS.search(text))


def _filler_in(text: str) -> list[str]:
    low = text.lower()
    return [f for f in FILLER if re.search(rf"\b{re.escape(f)}\b", low)]


def bullet_flags(text: str) -> list[str]:
    """What a recruiter skimming this bullet would miss."""
    flags = [] if has_number(text) else ["no number"]
    if text.lower().startswith(WEAK_OPENERS):
        flags.append("weak opener")
    return flags + [f"filler '{f}'" for f in _filler_in(text)]


def listed_tools(full_text: str) -> list[tuple[str, list[str]]]:
    """Items from a Tools or Skills line, each with the names that count as using it.

    'SQL (BigQuery)' counts as shown if either SQL or BigQuery appears.
    """
    items = []
    for line in full_text.splitlines():
        m = _TOOL_LINE.match(line)
        if not m:
            continue
        for raw in re.split(r"[,;|•]", m.group(1)):
            raw = raw.strip(" .")
            if not raw:
                continue
            names = [raw.split("(")[0]] + re.findall(r"\(([^)]*)\)", raw)
            items.append((raw, [n.strip() for name in names for n in name.split("/") if n.strip()]))
    return items


def tools_not_shown(full_text: str) -> list[str]:
    """Listed tools that nothing else on the page mentions (bullets, project lines)."""
    body = "\n".join(ln for ln in full_text.splitlines() if not _TOOL_LINE.match(ln))
    return [raw for raw, names in listed_tools(full_text)
            if not any(re.search(rf"(?<!\w){re.escape(n)}(?!\w)", body, re.I) for n in names)]


def bullet_report(path: str | Path) -> list[tuple[str, list[str]]]:
    """Every bullet in the PDF with its flags, for `check --bullets`."""
    import pymupdf
    with pymupdf.open(path) as doc:
        return [(b, bullet_flags(b)) for page in doc for b in bullets(_lines(page))]


def extract_text(path: str | Path) -> str:
    """The resume's text in the order an ATS would read it."""
    import pymupdf
    with pymupdf.open(path) as doc:
        return "\n".join(page.get_text() for page in doc)


def check(path: str | Path, max_pages: int = 1, jd_text: str | None = None,
          letter: bool = False, company: str = "") -> Report:
    """Run every check. letter=True skips the checks that only make sense for a resume."""
    import pymupdf
    rep = Report(path=str(path))
    with pymupdf.open(path) as doc:
        rep.pages = doc.page_count
        if doc.page_count > max_pages:
            rep.fails.append(f"{doc.page_count} pages (limit {max_pages})")
        full_text = ""
        all_bullets: list[str] = []
        top_third = ""
        for pno, page in enumerate(doc, start=1):
            text = page.get_text()
            full_text += text + "\n"
            rep.fails += text_fails(text, pno)
            rows = _lines(page)
            if not rows:
                continue
            all_bullets += bullets(rows)
            if pno == 1:
                top_third = "\n".join(r["text"] for r in rows if r["y0"] < page.rect.height / 3)
            right = max(r["x1"] for r in rows)
            for i, (prev, cur) in enumerate(zip(rows, rows[1:])):
                if i == len(rows) - 2 and letter:
                    continue  # a letter ends with a short signature line
                # A wrapped line follows a full-width line, starts at the same left
                # edge, uses the same font, and isn't bold (headings are bold).
                if (1 <= len(cur["text"].split()) <= 3 and prev["x1"] > right - 40
                        and abs(cur["x0"] - prev["x0"]) < 4
                        and cur["size"] == prev["size"] and not cur["bold"]):
                    rep.fails.append(f"page {pno}: line wraps with only '{cur['text']}' on it")
            # Stored order vs visual order: big jumps back up the page mean the
            # parser will read sections out of sequence.
            jumps = sum(1 for a, b in zip(rows, rows[1:]) if b["y0"] < a["y0"] - 100)
            if jumps:
                rep.warnings.append(
                    f"page {pno}: text is stored out of reading order (it jumps back up the page). "
                    "Multi-column layouts do this; a single column parses most reliably")
            if page.get_images():
                rep.warnings.append(f"page {pno}: contains an image. Text inside images is invisible to an ATS")

    letters = sum(ch.isalnum() for ch in full_text)
    if letters < 200:
        rep.fails.append("almost no selectable text. Is this a scanned image? An ATS will read it as blank")
        return rep

    head = "\n".join(full_text.strip().splitlines()[:12])
    if not _EMAIL.search(full_text):
        rep.fails.append("no email address found in the text")
    elif not _EMAIL.search(head):
        rep.warnings.append("email isn't near the top; some parsers only read contact details from the header")
    if not _PHONE.search(full_text):
        rep.warnings.append("no phone number found")

    lines = [re.sub(r"[^a-z ]", "", ln.lower()).strip() for ln in full_text.splitlines()]
    for section, names in ({} if letter else _SECTIONS).items():
        if not any(ln in names for ln in lines):
            rep.warnings.append(
                f"no standard '{section.title()}' heading on its own line; parsers use it to find that section")
    if not letter and not _DATE_RANGE.search(full_text):
        rep.warnings.append("no date ranges like 'Jan 2022 – Present' found; parsers use them to build your timeline")

    if not letter:
        _bullet_checks(rep, all_bullets, full_text)
    rep.info.append(f"{len(full_text.split())} words, {rep.pages} page(s)")
    if jd_text:
        from jobhunt import keywords
        ignore = (company,) if company else ()
        rep.keywords = keywords.coverage(jd_text, full_text, ignore=ignore)
        if not letter and top_third:
            top = keywords.coverage(jd_text, top_third, ignore=ignore)["covered"]
            rep.keywords["top_third"] = [t for t in rep.keywords["covered"] if t in top]
    return rep


def cut_order(path: str | Path, max_pages: int = 1, jd_text: str | None = None,
              letter_text: str | None = None, company: str = "") -> dict:
    """Which bullets to cut first when a resume runs long, weakest first.

    Each bullet is scored on what it does for this job: how many of the
    posting's top terms it uses, whether it carries a number, whether another
    bullet already says much the same, and whether the cover letter leans on
    it. The lowest score is the first to cut. A suggestion, not a verdict: the
    person may know a bullet matters more than its words show.
    """
    import pymupdf
    from jobhunt import keywords
    items: list[str] = []
    spill = 0
    with pymupdf.open(path) as doc:
        for pno, page in enumerate(doc, start=1):
            rows = _lines(page)
            items += bullets(rows)
            if pno > max_pages:
                spill += len(rows)
    terms = keywords.extract_terms(jd_text, top=30, ignore=(company,) if company else ()) if jd_text else []
    letter = keywords.content_stems(letter_text) if letter_text else set()
    letter_nums = set(re.findall(r"\d[\d.,]*%?", _YEAR.sub("", letter_text or "")))
    stems = [keywords.content_stems(b) for b in items]
    hits = [keywords.terms_in(terms, b) for b in items]
    top = max((len(h) for h in hits), default=0) or 1
    scored = []
    for i, b in enumerate(items):
        overlap, twin = 0.0, ""
        for j, other in enumerate(stems):
            if j != i and stems[i] and other:
                jac = len(stems[i] & other) / len(stems[i] | other)
                if jac > overlap:
                    overlap, twin = jac, items[j]
        nums = set(re.findall(r"\d[\d.,]*%?", _YEAR.sub("", b)))
        in_letter = bool(letter) and (bool(nums & letter_nums) or len(stems[i] & letter) >= 4)
        num = has_number(b)
        score = 3 * len(hits[i]) / top + (1 if num else 0) + (1 - overlap) + (1 if in_letter else 0)
        why = [f"{len(hits[i])} posting term{'s' if len(hits[i]) != 1 else ''}" if terms else "no posting given"]
        if not num:
            why.append("no number")
        if overlap >= 0.3:
            why.append(f"overlaps '{_short(twin, 5)}'")
        if in_letter:
            why.append("the cover letter uses it")
        scored.append((round(score, 1), b, why))
    scored.sort(key=lambda x: x[0])
    return {"spill_lines": spill, "bullets": scored, "terms": bool(terms)}


def _short(text: str, words: int = 6) -> str:
    parts = text.split()
    return " ".join(parts[:words]) + ("…" if len(parts) > words else "")


def _bullet_checks(rep: Report, items: list[str], full_text: str) -> None:
    """Recruiter-skim checks on the bullets. All are warnings: the person decides."""
    if not items:
        rep.info.append("no bullet points found, so the bullet checks were skipped")
        return
    numbered = [b for b in items if has_number(b)]
    share = len(numbered) / len(items)
    rep.info.append(f"{len(items)} bullets, {len(numbered)} with a number ({round(100 * share)}%)")
    if share < METRIC_TARGET:
        missing = [_short(b) for b in items if not has_number(b)]
        rep.warnings.append(
            f"only {len(numbered)} of {len(items)} bullets have a number (aim for 80%+). Add one only where "
            "you have a real, sourced result. Without a number: " + "; ".join(missing))
    weak = [_short(b, 4) for b in items if b.lower().startswith(WEAK_OPENERS)]
    if weak:
        rep.warnings.append("bullets that open with a duty, not an action (lead with a verb such as "
                            "Launched, Cut or Grew): " + "; ".join(weak))
    filler = sorted({f for b in items for f in _filler_in(b)})
    if filler:
        rep.warnings.append("filler a recruiter can't check: " + ", ".join(f"'{f}'" for f in filler))
    unshown = tools_not_shown(full_text)
    if unshown:
        rep.warnings.append("listed but never shown in a bullet: " + ", ".join(unshown)
                            + ". Name a tool in a bullet where you really used it, or drop it from the list")


def render(rep: Report) -> str:
    out = [f"FAIL: {m}" for m in rep.fails] + [f"WARN: {m}" for m in rep.warnings]
    out += [f"info: {m}" for m in rep.info]
    if rep.keywords:
        k = rep.keywords
        out.append(f"info: uses {len(k['covered'])} of the posting's top {len(k['terms'])} terms ({k['percent']}%)")
        if k["missing"]:
            out.append("      not in resume: " + ", ".join(k["missing"]))
            out.append("      Add one only where you have real experience behind it.")
        if "top_third" in k:
            top = k["top_third"]
            out.append(f"info: {len(top)} of the {len(k['covered'])} matched terms sit in the top third of page 1, "
                       "where a recruiter's first few seconds go" + (": " + ", ".join(top) if top else ""))
    out.append("OK" if rep.ok else f"{len(rep.fails)} problem(s) to fix")
    return "\n".join(out)
