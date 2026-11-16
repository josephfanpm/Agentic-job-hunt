# Agent contract

Any number of agents can work in this system: **Claude** (Claude Code), **Codex**, **Antigravity**, **Grok** (Grok Build), **Muse**, **Cline** with an open model, or any other agent that can run a command and edit the tracker. Each one can do every automated step: create the Google Sheet, run the scan, tailor, and apply. This contract keeps them from colliding and from wasting AI usage.

## Start here

0. If `private/` doesn't exist, the user hasn't set up yet: follow [prompts/setup.md](prompts/setup.md). If the user isn't technical, use plain language and run commands yourself.
1. Read `private/config.json`. `mode` tells you how much to do; follow the rules for that mode in [MODES.md](MODES.md). `tracker` tells you where records live: `csv` (files in `private/tracker/`) or `sheet` (a Google Sheet).
2. The user's facts are in `private/profile.md`. Use nothing that isn't there or in their own files. Tailor from its **Experience bank**; if that's empty, offer to run [prompts/profile-interview.md](prompts/profile-interview.md).
3. Each task has a file in `prompts/`. Follow it.

## Let the scripts do their work

These need no AI, so never do them by hand:

| Need | Run |
|---|---|
| New jobs, filtered, ranked, deduped | `python -m jobhunt scan` |
| LinkedIn searches for a job | `python -m jobhunt people "Company" "Title"` |
| Resume pre-flight and keyword gap | `python -m jobhunt check resume.pdf --jd <jd file>` |
| A company's job board | `python -m jobhunt boards add "Company"` |
| Requests that build the Google Sheet | `python -m jobhunt sheet` |
| Log an application (CSV tracker) | `python -m jobhunt applied "Company" "Role" --channel Referral` |
| Follow-ups due, channel results (CSV tracker) | `python -m jobhunt due`, `python -m jobhunt stats` |

The scan saves every job description to `private/jds/`. Read it from there before fetching anything.

## The tracker is the source of truth

Every job, application and contact lives in the tracker, built from [sheet/schema.json](sheet/schema.json). Don't keep separate lists.

## Rules for every agent

1. **Never reorder, delete or overwrite** rows or columns another agent wrote. New rows go directly under the header. Fill only blank cells in existing rows unless the user asks otherwise.
2. **Don't add jobs by hand** when the scan can: it remembers what it has shown, so nothing appears twice. If you add a job the user sent you, check Company + Role against the Daily jobs and Applied tabs first.
3. **Claim a job before working it.** Write your name and the date in the Notes column (`Claude 2026-11-15: tailoring`) so other agents skip it.
4. **Tailor only from a real job description:** the saved copy, or the posting you fetched. If you can't get it, leave the job for another agent or the user. Never write one from memory.
5. **Never invent** pay, dates, locations, employers, titles, tools or metrics. Leave the cell empty instead.
6. **Draft messages, never send them.** Put drafts in the tracker, or in Gmail as drafts if Gmail is connected ([prompts/check-email.md](prompts/check-email.md)). The user sends them.
7. **Ask the user** before answering sponsorship or work-authorization questions, and before submitting where a referral is possible.
8. **Log every application** the same day: date, company, role, pay, location, status, resume sent, link and Channel. Then take the job off Daily jobs: that list holds only jobs not yet applied to, and the Applied tab is the record. With the sheet receiver installed, ticking Applied does this automatically.
9. **Send script output unchanged.** When a script prepares a sheet update, pass it along as it is. Never hand-type batch requests; hand-typed batches shift rows.
10. **Save files with ATS-friendly names:** `First_Last_Resume_Company.pdf` and `First_Last_Cover_Letter_Company.pdf`. Use underscores; no dates or version numbers.
11. **Never try to get around a captcha, login wall or rate limit.** Hand the job back to the user.

## Who owns which columns

The schema marks each column with an owner: `scan` (written by the scan), `any` (any agent), or `user` (only the user edits it). When a column is added, record its owner in the schema.

## Before submitting an application

- [ ] Job description read from `private/jds/` or fetched, and saved
- [ ] Resume tailored, compiled, and passing `python -m jobhunt check`
- [ ] Cover letter, if the form accepts one (`check --letter`)
- [ ] Referral checked: if the user has a contact at the company, ask them before applying
- [ ] Form answers use only facts from `private/profile.md`; sponsorship questions go to the user
- [ ] Message drafted for one person on the team
- [ ] Application logged, with Channel
