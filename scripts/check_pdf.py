"""Check a compiled resume or cover letter PDF before sending it.

Fails when:
  - the PDF has more than one page (override with --max-pages)
  - the text contains fused ligatures (U+FB00-FB06). An ATS reads "staffing"
    as "sta?ing", so the keyword never matches. Fix: in the .tex, load
    fontspec with Ligatures=NoCommon (see resume/template.tex).
  - a line wraps with only 1-3 words on it (wasted space, looks sloppy)

Usage: python scripts/check_pdf.py file.pdf [--max-pages 1]
Requires: pip install pymupdf
"""
import argparse
import sys

import pymupdf as fitz

LIGATURES = {chr(c) for c in range(0xFB00, 0xFB07)}


def check(path, max_pages):
    doc = fitz.open(path)
    problems = []
    if doc.page_count > max_pages:
        problems.append(f"{doc.page_count} pages (max {max_pages})")
    for pno, page in enumerate(doc, start=1):
        text = page.get_text()
        found = sorted({ch for ch in text if ch in LIGATURES})
        if found:
            problems.append(f"page {pno}: ligature characters {found}")
        # Collect visual lines with left/right edges, font size and boldness
        rows = []
        for block in page.get_text("dict")["blocks"]:
            for ln in block.get("lines", []):
                # Skip empty spans and the bullet glyph itself
                spans = [sp for sp in ln["spans"] if sp["text"].strip()
                         and any(ch.isalnum() for ch in sp["text"])]
                if not spans:
                    continue
                text = " ".join(sp["text"].strip() for sp in spans)
                rows.append({"x0": spans[0]["bbox"][0], "x1": ln["bbox"][2], "text": text,
                             "size": round(spans[0]["size"], 1),
                             "bold": bool(spans[0]["flags"] & 16)})
        if not rows:
            continue
        right = max(r["x1"] for r in rows)
        for prev, cur in zip(rows, rows[1:]):
            # A wrapped line follows a full-width line, starts at the same left
            # edge, uses the same font, and isn't bold (headings are bold).
            if (1 <= len(cur["text"].split()) <= 3
                    and prev["x1"] > right - 40
                    and abs(cur["x0"] - prev["x0"]) < 4
                    and cur["size"] == prev["size"] and not cur["bold"]):
                problems.append(f"page {pno}: short wrap '{cur['text']}'")
    return problems


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("pdf")
    p.add_argument("--max-pages", type=int, default=1)
    a = p.parse_args()
    issues = check(a.pdf, a.max_pages)
    for i in issues:
        print("FAIL:", i)
    print("OK" if not issues else f"{len(issues)} problem(s)")
    sys.exit(1 if issues else 0)
