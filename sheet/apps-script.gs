/**
 * agentic-job-hunt: receive scan results and add them to this Google Sheet.
 *
 * Lets `python -m jobhunt scan` running on your own computer write to your
 * sheet without any Google Cloud setup. Paste this into the sheet's
 * Extensions > Apps Script, set TOKEN, and deploy it as a web app
 * (step-by-step: sheet/README-apps-script.md).
 *
 * What it does with each request:
 *   - checks the secret token
 *   - skips any job whose Company + Role is already in "Daily jobs" or "Applied"
 *   - inserts the rest directly under the header, newest on top, so rows
 *     another agent wrote are never reordered or overwritten
 *   - fills columns by header name, so extra columns (another agent's) are left blank
 *
 * It also keeps "Daily jobs" to jobs you haven't applied to yet. When the
 * Applied box is ticked, the job is logged in the "Applied" tab (if it isn't
 * there already) and its row leaves "Daily jobs". Ticking by hand moves it at
 * once; rows ticked by another agent, or already in "Applied", are cleared at
 * the start of each scan.
 *
 * Pick: tick the Pick box on the jobs you want, then tell your AI agent
 * "work my picks". `python -m jobhunt picks` asks this script for the ticked
 * rows. When the scan asks for it (email_digest in config), this script also
 * emails you the top new jobs. Each has a Pick link that opens a page with one
 * button, so an email security scanner opening the link can't pick a job.
 *
 * Old jobs you haven't applied to move to an "Archive" tab once they're older
 * than the scan's expire_after_days setting (default 14), counted from the
 * Posted date, or from Scanned when there's no posting date. Jobs at your
 * priority companies are kept. Archived jobs are never added again.
 */

const TOKEN = 'PASTE-YOUR-TOKEN-HERE';
const DAILY_TAB = 'Daily jobs';
const APPLIED_TAB = 'Applied';
const ARCHIVE_TAB = 'Archive';
const DEDUPE_TABS = ['Daily jobs', 'Applied', 'Archive'];
const FOLLOW_UP_DAYS = 7;

function doPost(e) {
  let body;
  try {
    body = JSON.parse(e.postData.contents);
  } catch (err) {
    return reply_({ ok: false, error: 'request was not JSON' });
  }
  if (!TOKEN || TOKEN === 'PASTE-YOUR-TOKEN-HERE' || body.token !== TOKEN) {
    return reply_({ ok: false, error: 'wrong or missing token' });
  }
  const lock = LockService.getDocumentLock();
  lock.waitLock(30000);
  try {
    if (body.action === 'picks') return reply_({ ok: true, picks: listPicks_() });
    const res = addRows_(body.rows || [], body.expire_after_days, body.keep_companies || []);
    if (res.ok && body.email && res.fresh && res.fresh.length) {
      try {
        res.emailed = sendDigest_(res.fresh, Number(body.email_top) || 10);
      } catch (err) {
        res.email_error = String(err);  // the rows are in; only the email failed
      }
    }
    delete res.fresh;
    return reply_(res);
  } catch (err) {
    return reply_({ ok: false, error: String(err) });
  } finally {
    lock.releaseLock();
  }
}

// Opening the web app URL shows it's running. A Pick link from the email
// opens a page with one button; only the button ticks the box.
function doGet(e) {
  const p = (e && e.parameter) || {};
  if (p.action === 'pick') return pickPage_(p.k || '', p.s || '');
  return reply_({ ok: true, message: 'agentic-job-hunt receiver is running' });
}

function addRows_(rows, expireDays, keepCompanies) {
  const ss = SpreadsheetApp.getActiveSpreadsheet();
  const sheet = ss.getSheetByName(DAILY_TAB);
  if (!sheet) return { ok: false, error: 'no tab named ' + DAILY_TAB };

  const moved = sweepApplied_(ss);
  const archived = expireOld_(ss, expireDays, keepCompanies);

  const seen = new Set();
  DEDUPE_TABS.forEach(function (name) {
    const tab = ss.getSheetByName(name);
    if (!tab || tab.getLastRow() < 2) return;
    const head = tab.getRange(1, 1, 1, tab.getLastColumn()).getValues()[0].map(String);
    const c = head.indexOf('Company');
    const r = head.indexOf('Role');
    if (c < 0 || r < 0) return;
    tab.getRange(2, 1, tab.getLastRow() - 1, tab.getLastColumn()).getValues()
      .forEach(function (row) { seen.add(key_(row[c], row[r])); });
  });

  const fresh = [];
  rows.forEach(function (row) {
    const k = key_(row.Company, row.Role);
    if (!seen.has(k)) {
      seen.add(k);
      fresh.push(row);
    }
  });
  if (!fresh.length) {
    return { ok: true, added: 0, skipped: rows.length, moved: moved, archived: archived, fresh: [] };
  }

  const headers = sheet.getRange(1, 1, 1, sheet.getLastColumn()).getValues()[0].map(String);
  const width = headers.length;
  const hadData = sheet.getLastRow() >= 2;
  sheet.insertRowsBefore(2, fresh.length);
  const target = sheet.getRange(2, 1, fresh.length, width);

  // Match the look of the existing rows, or set a plain default
  if (hadData) {
    sheet.getRange(2 + fresh.length, 1, 1, width)
      .copyTo(target, SpreadsheetApp.CopyPasteType.PASTE_FORMAT, false);
  } else {
    target.setFontWeight('normal').setBackground(null).setFontColor(null)
      .setWrap(true).setVerticalAlignment('top');
  }
  target.clearDataValidations();

  const values = fresh.map(function (row) {
    return headers.map(function (h) {
      const v = row[h];
      if (v === undefined || v === null) return '';
      if (h === 'Link' && typeof v === 'object') {
        return '=HYPERLINK("' + String(v.url).replace(/"/g, '%22') + '","' +
          String(v.label || 'Open').replace(/"/g, '') + '")';
      }
      if (Array.isArray(v)) return ''; // rich text, filled below
      return v;
    });
  });
  target.setValues(values);

  ['Pick', 'Applied'].forEach(function (name) {
    const i = headers.indexOf(name);
    if (i >= 0) sheet.getRange(2, i + 1, fresh.length, 1).insertCheckboxes();
  });

  const search = headers.indexOf('LinkedIn search');
  if (search >= 0) {
    const rich = fresh.map(function (row) {
      const lines = row['LinkedIn search'] || [];
      let text = '';
      const spans = [];
      lines.forEach(function (ln, i) {
        const start = text.length;
        text += ln.label + ': ' + ln.query + (i < lines.length - 1 ? '\n' : '');
        spans.push([start, start + ln.label.length + 2 + ln.query.length, ln.url]);
      });
      const b = SpreadsheetApp.newRichTextValue().setText(text);
      spans.forEach(function (s) { b.setLinkUrl(s[0], s[1], s[2]); });
      return [b.build()];
    });
    sheet.getRange(2, search + 1, fresh.length, 1).setRichTextValues(rich);
  }
  return { ok: true, added: fresh.length, skipped: rows.length - fresh.length,
           moved: moved, archived: archived, fresh: fresh };
}

// ---- Pick ------------------------------------------------------------------

// Daily-jobs rows ticked Pick and not Applied, as {header: value}.
function listPicks_() {
  const ss = SpreadsheetApp.getActiveSpreadsheet();
  const sheet = ss.getSheetByName(DAILY_TAB);
  if (!sheet || sheet.getLastRow() < 2) return [];
  const headers = sheet.getRange(1, 1, 1, sheet.getLastColumn()).getValues()[0].map(String);
  const pick = headers.indexOf('Pick'), applied = headers.indexOf('Applied');
  if (pick < 0) return [];
  const range = sheet.getRange(2, 1, sheet.getLastRow() - 1, headers.length);
  const values = range.getValues(), formulas = range.getFormulas();
  const tz = ss.getSpreadsheetTimeZone();
  const out = [];
  values.forEach(function (row, i) {
    if (row[pick] !== true || (applied >= 0 && row[applied] === true)) return;
    const obj = {};
    headers.forEach(function (h, j) {
      if (!h || h === 'Pick' || h === 'Applied') return;
      let v = row[j];
      const link = String(formulas[i][j] || '').match(/HYPERLINK\("([^"]+)"/i);
      if (link) v = link[1];
      if (v instanceof Date) v = Utilities.formatDate(v, tz, 'yyyy-MM-dd');
      obj[h] = v;
    });
    out.push(obj);
  });
  return out;
}

// A short signature per job, so a Pick link works only for that job and
// never reveals the token.
function sign_(k) {
  const raw = Utilities.computeHmacSha256Signature(String(k), TOKEN);
  return Utilities.base64EncodeWebSafe(raw).slice(0, 22);
}

function findDailyRow_(k) {
  const sheet = SpreadsheetApp.getActiveSpreadsheet().getSheetByName(DAILY_TAB);
  if (!sheet || sheet.getLastRow() < 2) return null;
  const headers = sheet.getRange(1, 1, 1, sheet.getLastColumn()).getValues()[0].map(String);
  const c = headers.indexOf('Company'), r = headers.indexOf('Role');
  const values = sheet.getRange(2, 1, sheet.getLastRow() - 1, headers.length).getValues();
  for (let i = 0; i < values.length; i++) {
    if (key_(values[i][c], values[i][r]) === k) {
      return { sheet: sheet, headers: headers, row: i + 2, company: values[i][c], role: values[i][r] };
    }
  }
  return null;
}

function pickPage_(k, s) {
  if (!k || s !== sign_(k)) return page_('This link is not valid.', '');
  const hit = findDailyRow_(k);
  if (!hit) return page_('This job is no longer on your list.', '<p>It may be applied to or archived already.</p>');
  const button =
    '<button id="b" onclick="go()">Pick this job</button><p id="m"></p>' +
    '<script>function go(){document.getElementById("b").disabled=true;' +
    'google.script.run.withSuccessHandler(function(t){document.getElementById("m").textContent=t;})' +
    '.pickJob(' + JSON.stringify(k) + ',' + JSON.stringify(s) + ');}</script>';
  return page_(esc_(hit.company) + ' — ' + esc_(hit.role), button);
}

// Called by the button on the pick page.
function pickJob(k, s) {
  if (!k || s !== sign_(k)) return 'This link is not valid.';
  const lock = LockService.getDocumentLock();
  lock.waitLock(30000);
  try {
    const hit = findDailyRow_(k);
    if (!hit) return 'This job is no longer on your list.';
    const col = hit.headers.indexOf('Pick');
    if (col < 0) return 'Your sheet has no Pick column. Add one to Daily jobs first.';
    hit.sheet.getRange(hit.row, col + 1).insertCheckboxes().setValue(true);
    return 'Picked. Tell your AI agent "work my picks" when you\'re ready.';
  } finally {
    lock.releaseLock();
  }
}

function page_(title, body) {
  const html = '<style>body{font-family:Arial,sans-serif;margin:32px 16px;max-width:520px;color:#1f2937}' +
    'button{font-size:16px;padding:12px 20px;border:0;border-radius:6px;background:#1f3863;color:#fff}' +
    'button:disabled{opacity:.5}</style><h2>' + title + '</h2>' + body;
  return HtmlService.createHtmlOutput(html).setTitle('Pick a job')
    .addMetaTag('viewport', 'width=device-width, initial-scale=1');
}

// ---- Morning email ---------------------------------------------------------

// Email the top new jobs to the sheet's owner. Returns how many were listed.
function sendDigest_(rows, top) {
  const url = ScriptApp.getService().getUrl();
  const list = rows.slice()
    .sort(function (a, b) { return (Number(a.Rank) || 999) - (Number(b.Rank) || 999); })
    .slice(0, top);
  const items = list.map(function (row) {
    const k = key_(row.Company, row.Role);
    const pick = url + '?action=pick&k=' + encodeURIComponent(k) + '&s=' + sign_(k);
    const link = row.Link && typeof row.Link === 'object' ? row.Link.url : row.Link;
    const facts = [row.Pay, row.Location, row['Work type']].filter(Boolean).map(esc_).join(' · ');
    return '<tr><td style="padding:12px 0;border-bottom:1px solid #e5e7eb">' +
      '<b>' + esc_(row.Company) + '</b> — ' + esc_(row.Role) + '<br>' +
      (facts ? '<span style="color:#4b5563">' + facts + '</span><br>' : '') +
      (row['Who you know'] ? 'You know: ' + esc_(row['Who you know']) + '<br>' : '') +
      (row['Why it fits'] ? '<span style="color:#4b5563">' + esc_(row['Why it fits']) + '</span><br>' : '') +
      '<a href="' + esc_(pick) + '">Pick this job</a>' +
      (link ? ' · <a href="' + esc_(link) + '">See the posting</a>' : '') +
      '</td></tr>';
  });
  const more = rows.length > list.length ? '<p>' + (rows.length - list.length) + ' more in your sheet.</p>' : '';
  const names = list.slice(0, 3).map(function (r) { return r.Company; }).join(', ');
  MailApp.sendEmail({
    to: Session.getEffectiveUser().getEmail(),
    subject: rows.length + ' new job' + (rows.length === 1 ? '' : 's') + ': ' + names,
    htmlBody: '<div style="font-family:Arial,sans-serif;max-width:600px">' +
      '<table style="border-collapse:collapse;width:100%">' + items.join('') + '</table>' + more +
      '<p><a href="' + esc_(SpreadsheetApp.getActiveSpreadsheet().getUrl()) + '">Open your sheet</a>. ' +
      'When you\'ve picked, tell your AI agent "work my picks".</p></div>',
  });
  return list.length;
}

function esc_(v) {
  return String(v === undefined || v === null ? '' : v)
    .replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/"/g, '&quot;');
}

// Runs by itself whenever you edit the sheet by hand.
function onEdit(e) {
  const range = e && e.range;
  if (!range || range.getSheet().getName() !== DAILY_TAB || range.getRow() < 2) return;
  const sheet = range.getSheet();
  const headers = sheet.getRange(1, 1, 1, sheet.getLastColumn()).getValues()[0].map(String);
  const col = headers.indexOf('Applied') + 1;
  if (!col || range.getColumn() > col || range.getLastColumn() < col) return;
  const ss = sheet.getParent();
  const rows = [];
  for (let r = range.getRow(); r <= range.getLastRow(); r++) {
    if (sheet.getRange(r, col).getValue() === true) rows.push(r);
  }
  moveToApplied_(ss, sheet, headers, rows);
}

// Clear rows that are ticked, or whose job is already in the Applied tab.
function sweepApplied_(ss) {
  const sheet = ss.getSheetByName(DAILY_TAB);
  if (!sheet || sheet.getLastRow() < 2) return 0;
  const headers = sheet.getRange(1, 1, 1, sheet.getLastColumn()).getValues()[0].map(String);
  const done = appliedKeys_(ss);
  const values = sheet.getRange(2, 1, sheet.getLastRow() - 1, headers.length).getValues();
  const a = headers.indexOf('Applied'), c = headers.indexOf('Company'), r = headers.indexOf('Role');
  const rows = [];
  values.forEach(function (row, i) {
    if (!row[c] && !row[r]) return;
    if ((a >= 0 && row[a] === true) || done.has(key_(row[c], row[r]))) rows.push(i + 2);
  });
  return moveToApplied_(ss, sheet, headers, rows);
}

function appliedKeys_(ss) {
  const keys = new Set();
  const tab = ss.getSheetByName(APPLIED_TAB);
  if (!tab || tab.getLastRow() < 2) return keys;
  const head = tab.getRange(1, 1, 1, tab.getLastColumn()).getValues()[0].map(String);
  const c = head.indexOf('Company'), r = head.indexOf('Role');
  if (c < 0 || r < 0) return keys;
  tab.getRange(2, 1, tab.getLastRow() - 1, tab.getLastColumn()).getValues()
    .forEach(function (row) { keys.add(key_(row[c], row[r])); });
  return keys;
}

// Log each row in the Applied tab if it's missing there, then delete it from Daily jobs.
function moveToApplied_(ss, sheet, headers, rowNumbers) {
  if (!rowNumbers.length) return 0;
  const tab = ss.getSheetByName(APPLIED_TAB);
  const done = appliedKeys_(ss);
  if (tab) {
    const aHead = tab.getRange(1, 1, 1, tab.getLastColumn()).getValues()[0].map(String);
    const tz = ss.getSpreadsheetTimeZone();
    const today = new Date();
    const follow = new Date(today.getTime() + FOLLOW_UP_DAYS * 86400000);
    rowNumbers.forEach(function (n) {
      const range = sheet.getRange(n, 1, 1, headers.length);
      const vals = range.getValues()[0];
      const formulas = range.getFormulas()[0];
      const get = function (h) {
        const i = headers.indexOf(h);
        return i < 0 ? '' : (formulas[i] || vals[i]);
      };
      if (done.has(key_(get('Company'), get('Role')))) return;
      const out = aHead.map(function (h) {
        switch (h) {
          case 'Applied': case 'Applied date': return Utilities.formatDate(today, tz, 'yyyy-MM-dd');
          case 'Status': return 'Applied';
          case 'Follow up on': return Utilities.formatDate(follow, tz, 'yyyy-MM-dd');
          case 'Resume sent': return get('Resume');
          case 'Notes': return 'Moved from Daily jobs when marked applied';
          default: return get(h);
        }
      });
      tab.appendRow(out);
      done.add(key_(get('Company'), get('Role')));
    });
  }
  // Delete from the bottom up so row numbers stay valid
  rowNumbers.slice().sort(function (x, y) { return y - x; })
    .forEach(function (n) { sheet.deleteRow(n); });
  return rowNumbers.length;
}

// Move unapplied jobs older than `days` to the Archive tab, except at kept companies.
function expireOld_(ss, days, keepCompanies) {
  days = Number(days);
  if (!days || days < 1) return 0;
  const sheet = ss.getSheetByName(DAILY_TAB);
  if (!sheet || sheet.getLastRow() < 2) return 0;
  const headers = sheet.getRange(1, 1, 1, sheet.getLastColumn()).getValues()[0].map(String);
  const width = headers.length;
  const p = headers.indexOf('Posted'), s = headers.indexOf('Scanned'), c = headers.indexOf('Company');
  const keep = (keepCompanies || []).map(function (k) { return norm_(k); }).filter(String);
  const cutoff = new Date(Date.now() - days * 86400000);
  const range = sheet.getRange(2, 1, sheet.getLastRow() - 1, width);
  const values = range.getValues();
  const formulas = range.getFormulas();
  const old = [];
  values.forEach(function (row, i) {
    if (!row[c]) return;
    const company = ' ' + norm_(row[c]) + ' ';
    if (keep.some(function (k) { return company.indexOf(' ' + k + ' ') >= 0; })) return;
    const when = asDate_(p >= 0 ? row[p] : '') || asDate_(s >= 0 ? row[s] : '');
    if (when && when < cutoff) old.push(i);
  });
  if (!old.length) return 0;

  let archive = ss.getSheetByName(ARCHIVE_TAB);
  if (!archive) {
    archive = ss.insertSheet(ARCHIVE_TAB);
    archive.getRange(1, 1, 1, width).setValues([headers]);
    sheet.getRange(1, 1, 1, width).copyTo(archive.getRange(1, 1, 1, width),
      SpreadsheetApp.CopyPasteType.PASTE_FORMAT, false);
    archive.setFrozenRows(1);
  }
  const aHead = archive.getRange(1, 1, 1, archive.getLastColumn()).getValues()[0].map(String);
  const out = old.map(function (i) {
    return aHead.map(function (h) {
      const j = headers.indexOf(h);
      return j < 0 ? '' : (formulas[i][j] || values[i][j]);
    });
  });
  archive.getRange(archive.getLastRow() + 1, 1, out.length, aHead.length).setValues(out);
  old.slice().reverse().forEach(function (i) { sheet.deleteRow(i + 2); });
  return old.length;
}

function asDate_(v) {
  if (v instanceof Date && !isNaN(v)) return v;
  const m = String(v || '').match(/(\d{4})-(\d{2})-(\d{2})/);
  return m ? new Date(Number(m[1]), Number(m[2]) - 1, Number(m[3])) : null;
}

function norm_(s) {
  return String(s || '').toLowerCase().replace(/[^a-z0-9]+/g, ' ').trim();
}

function key_(company, role) {
  const n = function (s) {
    return String(s || '').toLowerCase()
      .replace(/\bsr\b\.?/g, 'senior').replace(/[^a-z0-9]+/g, ' ').trim();
  };
  return n(company) + '|' + n(role);
}

function reply_(obj) {
  return ContentService.createTextOutput(JSON.stringify(obj))
    .setMimeType(ContentService.MimeType.JSON);
}
