# Daily scan

Run once a day on a schedule. Replace every `{{PLACEHOLDER}}` with your own values from `private/profile.md` before scheduling. It's written for an unattended run, so the agent doesn't ask questions.

---

You run {{NAME}}'s daily job scan and add new matches to their Google Sheet. Work without asking questions; nobody is watching this run. Another agent may also edit this sheet, so follow AGENTS.md: never reorder, delete or overwrite existing rows or columns.

**WHO THEY ARE:** {{ONE_LINE_BACKGROUND}}. Based in {{CITY}}; work authorization: {{WORK_AUTH}}. Pay floor: {{PAY_FLOOR}}. Target: {{TARGET_LEVELS}} roles in {{TARGET_SECTORS}}.

1. **SCRAPE.** Run `pip install -q python-jobspy`, then call `jobspy.scrape_jobs` with `site_name=["linkedin","indeed","glassdoor","zip_recruiter"]`, `hours_old=30`, `results_wanted=40` and `linkedin_fetch_description=False`, once per entry in {{SEARCHES}}. Each entry is a (search_term, location, country_indeed) triple, for example `('"product manager" healthcare', 'United States', 'USA')`. Wrap each search in try/except; if LinkedIn returns 429, keep going with the other boards. Dedupe by job_url and by (company, title).
   - **1b. Priority companies:** for each company in {{PRIORITY_COMPANIES}} that has a public job feed (for example `amazon.jobs/en/search.json`, `boards-api.greenhouse.io/v1/boards/<board>/jobs`, or `api.ashbyhq.com/posting-api/job-board/<org>`), fetch roles posted in the last 2 days that match the level filter. These skip the sector filter and rank first. Put the company's job ID at the start of the Message cell, so referrers can find the posting.
2. **FILTER.** Keep only {{TARGET_LEVELS}}. Drop {{EXCLUDED_LEVELS}}. Keep only companies in {{TARGET_SECTORS}}, including those teams inside large companies. Drop job aggregators unless you can name the real employer. When unsure about a company, run one quick web search.
3. **DEDUPE** against the sheet ({{SHEET_ID}}): read the Daily jobs and Applied tabs and skip any Company + Role already there.
4. **RANK** best fit first: priority companies, then {{FIT_ORDER}}. Break ties toward higher posted pay, then {{TIEBREAK}}. Rank restarts at 1 each day.
5. **WRITE.** Insert one blank row per new role directly under the Daily jobs header (insertDimension, startIndex 1, inheritFromBefore false), then write the rows from A2, best rank on top. Fill only the columns owned by `scan` in `sheet/schema.json`, and leave the rest empty. Write dates as yyyy-mm-dd. Write the Link as `=HYPERLINK("<url>","<source>")`. Why it fits is one short plain sentence; flag pay at or below the floor. Never invent pay, dates or locations.
6. **LINKEDIN SEARCH.** Fill the LinkedIn search cell for each new row by following `prompts/linkedin-search.md`, and build the request with `scripts/linkedin_search.py`.
7. **VERIFY.** Read the new rows back and fix anything wrong.

**RULES:** Leave a cell empty when the data isn't there. Don't touch the Applied or Network tabs except to read them. Don't edit earlier days' rows. If nothing new matches, write nothing. End with a two-line summary: postings scraped, rows added, and the top 3.
