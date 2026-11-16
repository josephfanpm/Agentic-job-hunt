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
 */

const TOKEN = 'PASTE-YOUR-TOKEN-HERE';
const DAILY_TAB = 'Daily jobs';
const DEDUPE_TABS = ['Daily jobs', 'Applied'];

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
    return reply_(addRows_(body.rows || []));
  } catch (err) {
    return reply_({ ok: false, error: String(err) });
  } finally {
    lock.releaseLock();
  }
}

// Lets you open the web app URL in a browser to confirm it's deployed.
function doGet() {
  return reply_({ ok: true, message: 'agentic-job-hunt receiver is running' });
}

function addRows_(rows) {
  const ss = SpreadsheetApp.getActiveSpreadsheet();
  const sheet = ss.getSheetByName(DAILY_TAB);
  if (!sheet) return { ok: false, error: 'no tab named ' + DAILY_TAB };

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
  if (!fresh.length) return { ok: true, added: 0, skipped: rows.length };

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

  const applied = headers.indexOf('Applied');
  if (applied >= 0) sheet.getRange(2, applied + 1, fresh.length, 1).insertCheckboxes();

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
  return { ok: true, added: fresh.length, skipped: rows.length - fresh.length };
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
