# Create the job search sheet

Any agent with a Google Sheets (or Google Drive) connector can run this. Skip it if you're happy with the default CSV tracker.

1. **Check first.** If `private/config.json` already has a `sheet_id`, open that sheet and stop. Never make a second one.
2. **Create an empty spreadsheet** named `Job search <year>` in the user's own Google Drive. If the connector is tied to a work account, ask the user which account to use first.
3. **Build the formatting requests** with the script; never write them by hand:
   ```
   python -m jobhunt sheet --rows 500 > requests.json
   ```
4. **Send `requests.json`** as one `batchUpdate` call, unchanged. It adds the three tabs with sheetIds 1, 2 and 3 and deletes the default "Sheet1", so run it on a brand-new file only.
5. **Verify:** read back row 1 of each tab and confirm it matches `sheet/schema.json`. Check that the dropdowns and checkboxes work.
6. **Save it:** set `"tracker": "sheet"` and `"sheet_id": "<id>"` in `private/config.json`, and give the user the link.

To add a column later, add it to the end of the tab in `sheet/schema.json` with an `owner`, then add the header and formatting to the live sheet.
