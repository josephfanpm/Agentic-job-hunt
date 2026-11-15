# LinkedIn Boolean searches

For each job, write three LinkedIn people searches, one for each kind of person who can help: **recruiters**, **hiring managers**, and **peers** already doing the job. Each one goes with a message template in [outreach.md](outreach.md).

## The pattern

Put every OR group in parentheses, before or between the ANDs. Never use a bare OR. Use quotes for phrases.

| Who | Search |
|---|---|
| Recruiters | `(recruiter OR "talent acquisition" OR sourcer) AND <company>` |
| Hiring managers | `("director of product" OR "head of product" OR "group product manager" OR "VP of product" OR "senior manager, product") AND <company> AND <team>` |
| Peers | `"product manager" AND <company> AND <team>` |

- `<company>`: the name in quotes if it has a space (`"CVS Health"`), bare if it doesn't (`DoorDash`). Use `(Brand OR Parent)` when both names appear.
- `<team>`: 2–3 words from the job title or posting, as one OR group, such as `(merchant OR marketplace OR consumer)`. Leave it out at small companies, or when the title doesn't name a team.
- **Large companies:** add `AND (product OR tech OR technical)` to the recruiter search, so it finds tech recruiters rather than warehouse or retail hiring.
- **Other functions:** the hiring manager titles follow your job title. A software engineer gets `("director of engineering" OR "engineering manager" ...)`. Set `linkedin.manager_titles` in your config to choose your own.

## In the sheet

Each cell holds three lines: `Recruiters: …`, `Hiring managers: …`, `Peers: …`. Each line links to `https://www.linkedin.com/search/results/people/?keywords=<url-encoded search>`. The scan fills this cell for every new job. For any other job, run `python -m jobhunt people "Company" "Job title"`.

## Tips for the user

- After a search opens, set LinkedIn's **Current company** filter. Keyword search also matches people who used to work there.
- If a search returns nothing, drop the team group and search again.
- Follow the company's LinkedIn page before you message anyone there.
- LinkedIn Premium shows how closely you're connected to someone (2nd or 3rd degree) and raises the search limits. It's worth it while you're actively searching.
