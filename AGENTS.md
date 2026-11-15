# Agent contract

Two agents work in this system: **Claude** (Claude Code, with the Google Sheets connector) and **Muse** (or any other agent that can browse and apply). Either one can do every automated step. This contract keeps them from colliding.

## The sheet is the source of truth

Every job, application and contact lives in one Google Sheet built from [sheet/schema.json](sheet/schema.json). Before writing, read the tabs you need. Don't keep separate lists.

## Rules for both agents

1. **Never reorder, delete or overwrite** rows or columns another agent wrote. Insert new rows under the header, and fill only blank cells in existing rows unless the user asks otherwise.
2. **Dedupe on Company + Role** across both the Daily jobs and Applied tabs before adding a job. Links are `HYPERLINK` formulas, so don't dedupe on links.
3. **Claim a job before working it.** Write your name and the date in the Notes column (`Claude 2026-11-15: tailoring`) so the other agent skips it.
4. **Tailor only from a fetched job description.** If you can't fetch the real posting, leave the job for the other agent or the user. Never write a job description from memory.
5. **Never invent** pay, dates, locations, employers, titles, tools or metrics. Leave the cell empty instead.
6. **Draft messages, never send them.** Put drafts in the sheet. The user sends them.
7. **Ask the user** before answering sponsorship or work-authorization questions, and before submitting where a referral is pending.
8. **Log every application** in the Applied tab on the same day: date, company, role, pay, location, status, resume sent, link and Channel.
9. **Write multi-row updates with a script**, not by hand. Hand-typed batches shift rows.
10. **Save files with ATS-friendly names**: `First_Last_Resume_Company.pdf` and `First_Last_Cover_Letter_Company.pdf`. Use underscores; no dates or version numbers.

## Who owns which columns

The schema marks each column with an owner: `scan` (whichever agent runs the daily scan), `any` (either agent), or `user` (only the user edits it). When columns are added later, record the owner in the schema.

## Auto-apply checklist

Before submitting:

- [ ] Job description fetched and saved
- [ ] Resume tailored, compiled, and passed `scripts/check_pdf.py`
- [ ] Cover letter, if the form accepts one
- [ ] Referral checked: if the user has a contact at the company, ask them before applying
- [ ] Form answers use only facts from `private/profile.md`; sponsorship questions go to the user
- [ ] Message drafted for one person on the team
- [ ] Applied tab row written, with Channel
