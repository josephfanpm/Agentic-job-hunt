# Create the job search sheet

Either agent can run this. It needs a Google Sheets (or Google Drive) connector.

1. **Check first.** If `private/profile.md` already has a sheet ID, open that sheet and stop. Never make a second sheet.
2. **Create an empty spreadsheet** named `Job search <year>` in the user's own Google Drive. If the connector is tied to a work account, ask the user which account to use first.
3. **Build the formatting requests** with the script; never write them by hand:
   ```
   python scripts/build_sheet_requests.py --rows 500 > requests.json
   ```
4. **Send `requests.json`** as one `batchUpdate` call (the Sheets connector's `update_spreadsheet`). The default "Sheet1" must still have sheetId 0, so do this on a brand-new file only.
5. **Verify:** read back row 1 of each tab and confirm it matches `sheet/schema.json`. Check that the dropdowns and checkboxes work.
6. **Save** the sheet ID and link to `private/profile.md`, and give the user the link.

To add a column later, add it to the end of the tab in `schema.json` with an `owner`, add the header and formatting to the live sheet, and tell the other agent by updating AGENTS.md if ownership changed.
