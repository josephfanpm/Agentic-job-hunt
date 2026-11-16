# Let the scan write to your Google Sheet (5 minutes, once)

Running `python -m jobhunt scan` on your own computer can add jobs straight to your Google Sheet. It needs no AI, no Google Cloud account and no connector. A small script inside your sheet receives the rows. It accepts them only with a secret key that you set, and it adds them the same way an agent would: under the header, skipping jobs already in the sheet.

## 1. Pick a secret key

Make up a long random string, or let Python make one:

```
python -c "import secrets; print(secrets.token_urlsafe(24))"
```

Put it in `private/config.json`:

```json
"tracker": "sheet",
"sheet_token": "the-key-you-picked",
```

## 2. Add the script to your sheet

1. Open your job search Google Sheet.
2. Click **Extensions → Apps Script**. A code editor opens in a new tab.
3. Delete everything in the editor, then paste in the contents of [apps-script.gs](apps-script.gs).
4. On the line `const TOKEN = 'PASTE-YOUR-TOKEN-HERE';`, replace `PASTE-YOUR-TOKEN-HERE` with your key, keeping the quotes.
5. Click the **Save** icon (the floppy disk).

## 3. Deploy it as a web app

1. Click the blue **Deploy** button (top right) → **New deployment**.
2. Click the gear next to **Select type** → **Web app**.
3. Set **Execute as:** *Me*, and **Who has access:** *Anyone*. "Anyone" lets your computer reach it without signing in; the secret key is what keeps others out.
4. Click **Deploy**, then **Authorize access**, and choose your Google account.
   - If Google shows "Google hasn't verified this app", click **Advanced → Go to (project name) (unsafe)**. It's your own script, running in your own account.
5. Copy the **Web app URL**. It ends in `/exec`.

Put it in `private/config.json`:

```json
"sheet_webhook": "https://script.google.com/macros/s/.../exec",
```

## 4. Test it

```
python -m jobhunt scan
```

The last lines should say `sheet: added N row(s)`. Open the sheet: new jobs are at the top of **Daily jobs**, each with a checkbox, a link and three LinkedIn searches.

## Good to know

- **Columns are matched by header name.** Rename a column, and the scan stops filling it. Extra columns, such as another agent's, are left blank.
- **Jobs already in Daily jobs, Applied or Archive are skipped,** matched on Company + Role.
- **Applied jobs leave Daily jobs.** Ticking **Applied** moves the row to the Applied tab straight away, adding it there if it's missing. Rows ticked by another agent are moved at the next scan.
- **Old jobs are archived.** Jobs you haven't applied to move to an **Archive** tab once they're older than `expire_after_days` (default 14). Age is counted from Posted, or from Scanned when there's no posting date. Companies in `priority_companies` are kept. Set it to 0 to keep everything.
- **If you edit the script later,** use **Deploy → Manage deployments → Edit → Version: New version**. That keeps the same URL.
- **If the sheet can't be reached,** the scan keeps those jobs and offers them again next time.
- **To turn it off,** use **Deploy → Manage deployments → Archive**.
