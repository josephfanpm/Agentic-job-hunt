"""Read the questions on an application page and enter the bank's answers.

`scan` lists every control a person could fill in, grouped into questions with their
labels and options. `fill` answers each from the job's own answers and the answer bank.
A required question with no safe answer is reported, never guessed.
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field

from . import answers as bank

# Ticking one of these is the user's decision, never the tool's.
AGREEMENT_STOP = ("arbitration", "non-compete", "noncompete", "non compete", "background check",
                  "electronic signature", "e-signature", "legally binding", "waive")

SCAN_JS = r"""
(extraCombo) => {
  let n = +(document.body.dataset.jhn || 0);
  const tag = e => { if (!e.dataset.jh) { e.dataset.jh = String(++n); } return e.dataset.jh; };
  const txt = e => e ? (e.innerText || e.textContent || '').replace(/\s+/g, ' ').trim() : '';
  const shown = e => {
    if (!e) return false;
    const s = getComputedStyle(e);
    if (s.display === 'none' || s.visibility === 'hidden') return false;
    const r = e.getBoundingClientRect();
    return r.width > 0 && r.height > 0;
  };
  const anyShown = e => shown(e) || shown(e.closest('label')) || shown(e.parentElement)
    || (e.parentElement && shown(e.parentElement.parentElement));
  const byId = id => id ? document.querySelector('label[for="' + CSS.escape(id) + '"]') : null;
  const labelled = e => {
    const lb = e.getAttribute && e.getAttribute('aria-labelledby');
    if (lb) { const t = lb.split(/\s+/).map(i => txt(document.getElementById(i))).join(' ').trim(); if (t) return t; }
    return (e.getAttribute && e.getAttribute('aria-label')) || '';
  };
  const optLabel = e => txt(byId(e.id)) || txt(e.closest('label')) || e.getAttribute('aria-label') || e.value || '';
  const BOX = '.ashby-application-form-field-entry, .application-question, .application-additional';
  const boxLabel = e => {
    const box = e.closest(BOX);
    if (!box) return '';
    return txt(box.querySelector('.ashby-application-form-question-title, .application-label')) || '';
  };
  const groupLabel = els => {
    const first = els[0];
    const fs = first.closest('fieldset, [role=radiogroup], [role=group]');
    if (fs) { const t = txt(fs.querySelector('legend')) || labelled(fs); if (t) return t; }
    const opts = new Set(els.map(optLabel));
    for (let p = first.parentElement, d = 0; p && p !== document.body && d < 8; p = p.parentElement, d++) {
      if (!els.every(x => p.contains(x))) continue;
      for (const c of p.querySelectorAll('legend, label, h1, h2, h3, h4, h5, h6, p, span, div')) {
        if (els.some(x => c.contains(x))) continue;
        const t = txt(c);
        if (!t || opts.has(t) || t.length > 600) continue;
        if (!(c.compareDocumentPosition(first) & Node.DOCUMENT_POSITION_FOLLOWING)) continue;
        return t;
      }
    }
    return '';
  };
  const oneLabel = e => boxLabel(e) || txt(byId(e.id)) || labelled(e) || txt(e.closest('label')) || groupLabel([e])
    || e.placeholder || e.name || '';
  const isReq = (e, label) => {
    if (e.required || e.getAttribute('aria-required') === 'true' || /[*✱]/.test(label)) return true;
    const box = e.closest(BOX);
    return !!(box && box.querySelector('.ashby-application-form-question-title[class*="required"], label[class*="required"], .required'));
  };
  const out = [];
  const seen = new Set();
  const skipType = new Set(['hidden', 'submit', 'button', 'image', 'reset', 'search', 'password']);
  for (const c of document.querySelectorAll('input, textarea, select, .ashby-application-form-input-yesno')) {
    if (c.disabled || c.closest('header, nav, footer, [class*="captcha"], .g-recaptcha, .h-captcha')) continue;
    if (c.tagName === 'INPUT' && c.closest('.ashby-application-form-input-yesno')) continue;
    const cls = c.getAttribute('class') || '';
    if (/requiredInput|iti__search|visually-hidden-input/.test(cls) || /captcha/i.test(c.name || '')) continue;
    if (c.matches('.ashby-application-form-input-yesno')) {
      const btns = [...c.querySelectorAll('button')];
      const label = boxLabel(c) || groupLabel(btns);
      out.push({kind: 'buttons', label, required: isReq(c, label), jh: tag(c), id: '', name: '',
        options: btns.map(b => ({text: txt(b), jh: tag(b), on: b.getAttribute('aria-pressed') === 'true'
          || /active|selected/i.test(b.getAttribute('class') || '')}))});
      continue;
    }
    const type = (c.getAttribute('type') || c.tagName).toLowerCase();
    if (skipType.has(type)) continue;
    if (type === 'file') {
      const box = c.closest(BOX + ', .file-upload, [class*="upload"], fieldset, div');
      const label = boxLabel(c) || labelled(c) || txt(byId(c.id)) || txt(box && box.querySelector('label, legend')) || '';
      out.push({kind: 'file', label, required: isReq(c, label), jh: tag(c), id: c.id || '', name: c.name || '', options: []});
      continue;
    }
    if (!anyShown(c)) continue;
    if (type === 'radio' || type === 'checkbox') {
      let els = c.name ? [...document.querySelectorAll('input[type="' + type + '"]')].filter(x => x.name === c.name) : [c];
      if (type === 'checkbox' && els.length < 2) {
        const box = c.closest(BOX + ', fieldset, [role=group]');
        const sibs = box ? [...box.querySelectorAll('input[type="checkbox"]')] : [];
        els = sibs.length > 1 && sibs.includes(c) ? sibs : [c];
      }
      const key = type + ':' + els.map(tag).join(',');
      if (seen.has(key)) continue;
      seen.add(key);
      if (type === 'checkbox' && els.length === 1) {
        const label = optLabel(c) || boxLabel(c) || groupLabel([c]);
        const around = txt(c.closest('label, ' + BOX) || c.parentElement && c.parentElement.parentElement).slice(0, 1500);
        out.push({kind: 'check', label: label.length > 2 ? label : around, context: around, required: isReq(c, label),
          jh: tag(c), id: c.id || '', name: c.name || '', options: [], on: c.checked});
        continue;
      }
      const label = boxLabel(c) || groupLabel(els);
      out.push({kind: type === 'radio' ? 'radio' : 'checks', label, required: els.some(x => isReq(x, label)),
        jh: tag(els[0]), id: '', name: c.name || '',
        options: els.map(x => ({text: optLabel(x), jh: tag(x), on: x.checked}))});
      continue;
    }
    const label = oneLabel(c);
    if (c.tagName === 'SELECT') {
      out.push({kind: 'select', label, required: isReq(c, label), jh: tag(c), id: c.id || '', name: c.name || '',
        value: c.selectedIndex > 0 ? txt(c.options[c.selectedIndex]) : '',
        options: [...c.options].filter(o => o.value !== '' && txt(o)).map(o => ({text: txt(o), jh: ''}))});
      continue;
    }
    const combo = c.getAttribute('role') === 'combobox' || /select__input/.test(cls)
      || c.getAttribute('aria-autocomplete') === 'list' || (extraCombo && c.matches(extraCombo));
    let value = c.value || '';
    if (combo) {
      const ctl = c.closest('.select__control');
      const v = ctl && ctl.querySelector('.select__single-value, .select__multi-value');
      value = v ? txt(v) : value;
    }
    out.push({kind: combo ? 'combo' : (c.tagName === 'TEXTAREA' ? 'textarea' : 'text'), label, required: isReq(c, label),
      jh: tag(c), id: c.id || '', name: c.name || '', value, options: [], type});
  }
  document.body.dataset.jhn = String(n);
  return out;
}
"""

OPTIONS_JS = r"""
() => {
  let n = +(document.body.dataset.jhn || 0);
  const out = [];
  for (const o of document.querySelectorAll('.select__menu [role=option], [role=listbox] [role=option], [role=option], .dropdown-location')) {
    const s = getComputedStyle(o); const r = o.getBoundingClientRect();
    if (s.display === 'none' || s.visibility === 'hidden' || r.width === 0 || r.height === 0) continue;
    if (!o.dataset.jh) o.dataset.jh = String(++n);
    const t = (o.innerText || '').replace(/\s+/g, ' ').trim();
    if (t && !out.some(x => x.jh === o.dataset.jh)) out.push({text: t, jh: o.dataset.jh});
  }
  document.body.dataset.jhn = String(n);
  return out;
}
"""


@dataclass
class Report:
    entered: list = field(default_factory=list)     # (question, answer)
    pending: list = field(default_factory=list)     # (question, options, why)
    blockers: list = field(default_factory=list)    # things only the user can decide
    done: set = field(default_factory=set)

    @property
    def ok(self) -> bool:
        return not self.pending and not self.blockers


@dataclass
class Context:
    entries: list                 # the answer bank
    job: list                     # this job's own answers, tried first
    resume: str = ""
    cover: str = ""
    country: str = ""
    company: str = ""
    url: str = ""
    extra_combo: str = ""


def job_entries(mapping: dict) -> list[dict]:
    """{"phrase from the question": "answer"} -> bank-style entries."""
    return [{"ask": [k], "answer": v} for k, v in (mapping or {}).items()]


def _el(page, jh: str):
    return page.locator(f'[data-jh="{jh}"]').first


def _resolve(q: dict, ctx: Context, many: bool = False):
    opts = [o["text"] for o in q.get("options") or []] or None
    for entries in (ctx.job, ctx.entries):
        if bank.find(q["label"], entries, ctx.country) is not None:
            return bank.resolve(q["label"], entries, opts, ctx.country, many=many)
    return None, None


def _file_kind(q: dict) -> str:
    hay = " ".join([q["label"], q["id"], q["name"]]).lower()
    if "cover" in hay:
        return "cover"
    if re.search(r"resume|résumé|\bcv\b|curriculum", hay):
        return "resume"
    return ""


def _combo(page, q: dict, ctx: Context):
    """A type-to-search or dropdown box. Returns (chosen text or None, options seen)."""
    box = _el(page, q["jh"])
    box.scroll_into_view_if_needed()
    try:
        box.click(timeout=5000)
    except Exception:
        box.focus()
        page.keyboard.press("ArrowDown")
    page.wait_for_timeout(400)
    seen = page.evaluate(OPTIONS_JS)
    entry = None
    for entries in (ctx.job, ctx.entries):
        entry = bank.find(q["label"], entries, ctx.country)
        if entry:
            break
    if not entry or entry.get("answer") in (None, "", []):
        page.keyboard.press("Escape")
        return None, [o["text"] for o in seen]
    wanted = entry["answer"] if isinstance(entry["answer"], list) else [entry["answer"]]
    hits = bank.choose(wanted, [o["text"] for o in seen])
    if not hits:
        for w in wanted:                       # a search box: type the answer, then pick from what comes back
            typed = str(w).split(",")[0][:30]
            box.fill("")
            box.press_sequentially(typed, delay=50)
            page.wait_for_timeout(1800)
            seen = page.evaluate(OPTIONS_JS)
            hits = bank.choose(wanted, [o["text"] for o in seen])
            if hits:
                break
    if not hits:
        try:
            box.fill("")
        except Exception:
            pass
        page.keyboard.press("Escape")
        return None, [o["text"] for o in seen]
    opt = next(o for o in seen if o["text"] == hits[0])
    o = _el(page, opt["jh"])
    o.scroll_into_view_if_needed()
    o.click(timeout=8000)
    page.wait_for_timeout(300)
    return hits[0], [x["text"] for x in seen]


def scan(page, extra_combo: str = "") -> list[dict]:
    return page.evaluate(SCAN_JS, extra_combo)


def fill(page, ctx: Context, report: Report | None = None, only_files: bool = False) -> Report:
    """One pass over the page. Call again after it, since answers can reveal new questions.
    `only_files` uploads the resume and cover letter and leaves every other question for later."""
    rep = report or Report()
    answered_labels = {bank.norm(q) for q, _ in rep.entered}
    for q in scan(page, ctx.extra_combo):
        if only_files and q["kind"] != "file":
            continue
        key = (q["kind"], bank.norm(q["label"]), q["id"] or q["name"])
        if key in rep.done:
            continue
        rep.done.add(key)
        label = re.sub(r"\s+", " ", q["label"]).strip() or q["name"] or q["id"] or "(no label)"
        kind = q["kind"]
        opts = [o["text"] for o in q.get("options") or []]

        def missing(why=""):
            if q["required"]:
                rep.pending.append((label, opts, why))
            else:
                rep.entered.append((label, "left blank (optional, no saved answer)"))

        try:
            if kind == "file":
                which = _file_kind(q)
                path = {"resume": ctx.resume, "cover": ctx.cover}.get(which, "")
                if path:
                    _el(page, q["jh"]).set_input_files(path)
                    page.wait_for_timeout(2500)
                    rep.entered.append(("Resume" if which == "resume" else "Cover letter", path.replace("\\", "/").split("/")[-1]))
                elif q["required"] and which != "resume":
                    rep.pending.append((label or "file upload", [], "the form requires a file the run was not given"))
                continue
            if kind in ("text", "textarea") and bank.norm(label) in answered_labels:
                continue        # the free-text twin of a choice already answered ("Other: ...")
            if kind in ("text", "textarea"):
                val, _ = _resolve(q, ctx)
                if val is None:
                    if q.get("value"):
                        rep.entered.append((label, q["value"] + "  (already on the form)"))
                    else:
                        missing("needs a written answer" if kind == "textarea" else "")
                    continue
                _el(page, q["jh"]).fill(val)
                rep.entered.append((label, val))
            elif kind == "select":
                val, _ = _resolve(q, ctx)
                if not val:
                    if q.get("value"):
                        rep.entered.append((label, q["value"] + "  (already on the form)"))
                    else:
                        missing()
                    continue
                _el(page, q["jh"]).select_option(label=val[0])
                rep.entered.append((label, val[0]))
            elif kind == "combo":
                chosen, seen = _combo(page, q, ctx)
                if chosen:
                    rep.entered.append((label, chosen))
                elif q.get("value"):
                    rep.entered.append((label, q["value"] + "  (already on the form)"))
                else:
                    opts = seen
                    missing()
            elif kind in ("radio", "checks", "buttons"):
                val, _ = _resolve(q, ctx, many=(kind == "checks"))
                if not val:
                    on = [o["text"] for o in q["options"] if o.get("on")]
                    if on:
                        rep.entered.append((label, ", ".join(on) + "  (already on the form)"))
                    else:
                        missing()
                    continue
                for v in val:
                    o = next(o for o in q["options"] if o["text"] == v)
                    if o.get("on"):
                        continue
                    if kind == "buttons":
                        _el(page, o["jh"]).click()
                    else:
                        _el(page, o["jh"]).evaluate("e => e.click()")
                    page.wait_for_timeout(150)
                rep.entered.append((label, ", ".join(val)))
            elif kind == "check":
                text = (q.get("context") or label).lower()
                if any(w in text for w in AGREEMENT_STOP):
                    rep.blockers.append("An agreement only you can accept: " + (q.get("context") or label)[:300])
                    continue
                val, _ = _resolve(q, ctx)
                want = bank.as_bool(val) if val is not None else None
                if want is None:
                    missing("a tick box with no saved answer")
                    continue
                if want != bool(q.get("on")):
                    _el(page, q["jh"]).evaluate("e => e.click()")
                rep.entered.append((label[:200], "ticked" if want else "left unticked"))
            answered_labels.add(bank.norm(label))
        except Exception as exc:  # one odd control must not hide the rest of the form
            rep.blockers.append(f"Could not fill '{label[:80]}': {type(exc).__name__} {str(exc)[:120]}")
    return rep
