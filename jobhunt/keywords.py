"""Rough keyword gap between a job description and a resume. No AI calls.

This is a counting heuristic, not a judgment. It lists terms the posting
leans on and whether the resume uses them, so a person (or an agent) can
decide which gaps are real experience worth adding and which to ignore.
Never add a term the resume's owner can't back up.
"""
from __future__ import annotations

import re
from collections import Counter

from jobhunt.text import drop_boilerplate

STOP = set("""a about above across after again all also an and any are as at be because been before
being below between both but by can could did do does doing down during each few for from further
had has have having he her here hers him his how i if in into is it its just may me might more most
must my no nor not of off on once only or other our ours out over own per same she should so some
such than that the their theirs them then there these they this those through to too under until up
upon us very via was we were what when where which while who whom why will with within without
would you your yours etc eg ie including include includes ensure ensuring across well new using use
used strong highly ability able work working works role roles team teams company join looking
experience experienced years year plus preferred required requirements qualifications
responsibilities what's you'll you're we're we'll our need needs help helps make makes build builds
building drive drives driving lead leads leading partner partners partnering closely day every
great best good excellent proven track record deep understanding knowledge skills skill
opportunity opportunities benefits salary range base equity bonus employer equal apply applicants
applicant status regard race color religion sex gender national origin disability veteran
identity orientation age law laws accommodation accommodations position job candidate candidates
based people one two three within like want get take across both many much other others""".split())

_WORD = re.compile(r"[A-Za-z][A-Za-z0-9+#./&-]*[A-Za-z0-9+#]|[A-Za-z]")


def _tokens(text: str) -> list[str]:
    return [t.strip(".-/") for t in _WORD.findall(text)]


def _stem(w: str) -> str:
    w = w.lower()
    for suf in ("ies", "es", "s"):
        if len(w) > 4 and w.endswith(suf) and not w.endswith("ss"):
            return w[: -len(suf)] + ("y" if suf == "ies" else "")
    return w


def _toolish(tok: str) -> bool:
    """SQL, A/B, B2B, Figma-style proper nouns mid-sentence, C++."""
    return (len(tok) > 1 and tok.isupper()) or bool(re.search(r"[0-9+#/]", tok)) \
        or bool(re.search(r"[a-z][A-Z]", tok))


def extract_terms(jd: str, top: int = 20, ignore: tuple[str, ...] = ()) -> list[str]:
    """The posting's most leaned-on terms: repeated words and phrases, plus tool names.

    `ignore` holds words to skip, such as the employer's own name.
    """
    skip = STOP | {w.lower() for name in ignore for w in name.split()}
    toks = _tokens(drop_boilerplate(jd))
    low = [t.lower() for t in toks]
    counts: Counter = Counter()
    display: dict[str, str] = {}

    def add(key: str, shown: str, weight: float):
        counts[key] += weight
        display.setdefault(key, shown)

    for i, t in enumerate(low):
        if t in skip or (len(t) < 3 and not _toolish(toks[i])):
            continue
        add(_stem(t), toks[i] if _toolish(toks[i]) else t, 1.0)
        for n, w in ((2, 1.6),):
            gram = low[i:i + n]
            if len(gram) == n and all(len(g) > 2 and g not in skip for g in gram):
                add(" ".join(_stem(g) for g in gram), " ".join(gram), w)

    tool_keys = {_stem(t.lower()) for t in toks if _toolish(t) and t.lower() not in skip}
    scored = []
    for key, score in counts.items():
        n = key.count(" ") + 1
        uses = score / {1: 1.0, 2: 1.6}[n]
        if uses >= 2 or (n == 1 and key in tool_keys):
            scored.append((score, key))
    scored.sort(reverse=True)

    picked: list[str] = []
    for _, key in scored:
        # skip single words already covered by a chosen phrase, and vice versa
        if any(key in p.split() or (" " in key and set(key.split()) <= set(p.split())) for p in picked):
            continue
        picked.append(key)
        if len(picked) >= top:
            break
    return [display[k] for k in picked]


def coverage(jd: str, resume: str, top: int = 20, ignore: tuple[str, ...] = ()) -> dict:
    """Which of the posting's terms appear in the resume."""
    terms = extract_terms(jd, top, ignore)
    resume_stems = [_stem(t) for t in _tokens(resume)]
    hay = " " + " ".join(resume_stems) + " "
    covered, missing = [], []
    for term in terms:
        needle = " " + " ".join(_stem(w) for w in term.split()) + " "
        (covered if needle in hay else missing).append(term)
    pct = round(100 * len(covered) / len(terms)) if terms else 0
    return {"terms": terms, "covered": covered, "missing": missing, "percent": pct}


def common_terms(postings: list[tuple[str, str]], min_postings: int = 3, top: int = 30) -> list[tuple[str, int]]:
    """Terms that several postings for the same kind of role share.

    `postings` holds (job description, company) pairs. A term counts once per
    posting. Terms most postings share describe the role itself, not one
    company's wording, so they belong in a base resume (where true).
    """
    seen: Counter = Counter()
    shown: dict[str, str] = {}
    for jd, company in postings:
        terms = extract_terms(jd, top=top, ignore=(company,) if company else ())
        for key in {" ".join(_stem(w) for w in t.split()): t for t in terms}.items():
            seen[key[0]] += 1
            shown.setdefault(key[0], key[1])
    return sorted(((shown[k], n) for k, n in seen.items() if n >= min_postings), key=lambda x: (-x[1], x[0]))
