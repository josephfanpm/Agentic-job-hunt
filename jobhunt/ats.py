"""ATS pre-flight: read a resume PDF the way an applicant tracking system does.

An ATS doesn't see your layout. It pulls the text out of the PDF in stored
order and looks for contact details, section headings, dates and keywords.
This check does the same and reports what a parser would trip on.

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
    rows = []
    for block in page.get_text("dict")["blocks"]:
        for ln in block.get("lines", []):
            spans = [sp for sp in ln["spans"] if sp["text"].strip()
                     and any(ch.isalnum() for ch in sp["text"])]
            if not spans:
                continue
            rows.append({
                "x0": spans[0]["bbox"][0], "x1": ln["bbox"][2], "y0": ln["bbox"][1],
                "text": " ".join(sp["text"].strip() for sp in spans),
                "size": round(spans[0]["size"], 1), "bold": bool(spans[0]["flags"] & 16),
            })
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
        for pno, page in enumerate(doc, start=1):
            text = page.get_text()
            full_text += text + "\n"
            rep.fails += text_fails(text, pno)
            rows = _lines(page)
            if not rows:
                continue
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

    rep.info.append(f"{len(full_text.split())} words, {rep.pages} page(s)")
    if jd_text:
        from jobhunt import keywords
        rep.keywords = keywords.coverage(jd_text, full_text, ignore=(company,) if company else ())
    return rep


def render(rep: Report) -> str:
    out = [f"FAIL: {m}" for m in rep.fails] + [f"WARN: {m}" for m in rep.warnings]
    out += [f"info: {m}" for m in rep.info]
    if rep.keywords:
        k = rep.keywords
        out.append(f"info: uses {len(k['covered'])} of the posting's top {len(k['terms'])} terms ({k['percent']}%)")
        if k["missing"]:
            out.append("      not in resume: " + ", ".join(k["missing"]))
            out.append("      Add one only where you have real experience behind it.")
    out.append("OK" if rep.ok else f"{len(rep.fails)} problem(s) to fix")
    return "\n".join(out)
