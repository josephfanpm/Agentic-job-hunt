# agentic-job-hunt

A job search run by two AI agents and one human. The agents find roles, tailor resumes, draft outreach and submit applications. The human picks the jobs, sends the messages and does the interviews.

I built this for my own search as a Senior Product Manager. Anyone can reuse it: swap in your own resume, targets and pay floor.

## What it does

| Stage | What happens | Who |
|---|---|---|
| **1. Set up** | Creates the Google Sheet the whole system runs on: tabs, columns, dropdowns and checkboxes | Claude or Muse |
| **2. Scan** | A daily scheduled run pulls new roles from LinkedIn, Indeed, Glassdoor, ZipRecruiter and company job boards, filters them to your targets, ranks them and adds them to the sheet | Claude or Muse |
| **3. Find people** | Writes three LinkedIn Boolean searches per job (recruiters, hiring managers, peers), each a one-click link | Claude or Muse |
| **4. Mine your network** | Scores every LinkedIn connection 1–5 against your goal and drafts an opener for each strong match | Claude |
| **5. Tailor** | Builds a one-page LaTeX resume and cover letter per job from the real job description, then checks the PDF for ATS problems | Claude or Muse |
| **6. Reach out** | Drafts a referral or hiring-manager message that fits the person reading it | Claude or Muse drafts, **you send** |
| **7. Apply** | Fills and submits the application, then logs it in the Applied tab with the channel used | Claude or Muse |
| **8. Interview** | Builds a story bank and practice plan from your resume and the job description | Claude |

**Both agents can do every automated step**: create the sheet, scan, tailor, and auto-apply. They share one sheet and follow one contract ([AGENTS.md](AGENTS.md)), so they never overwrite each other's work. Run either one alone, or both side by side.

## The rules that make it work

- **You pick, agents execute.** The scan gives you a short ranked list. You tick the jobs you want, and the agents do the rest.
- **Referral before application.** For big companies, line up a referral first. Apply cold only where the fit is strong. The Applied tab records the channel for each application (Referral, Hiring manager message, Cold application, Auto-apply), so you can see which one actually gets interviews.
- **Message a person for every application.** Each job gets a short, specific message to someone on that team.
- **Never invent anything.** Agents tailor only from a job description they actually fetched, and only with facts and numbers from your own files. Titles, dates, employers, tools and metrics never get made up.
- **Agents draft, you send.** No message goes out under your name without you.
- **Ask before sponsorship answers.** Work-authorization questions go to you.

## Setup

1. **Clone this repo**, then copy `examples/profile.example.md` to `private/profile.md` and fill it in. `private/` is git-ignored.
2. **Connect Google Sheets** to each agent (for Claude: the Google Sheets connector).
3. **Create the sheet.** Ask either agent: *"Run prompts/create-sheet.md."* It builds the tabs from [sheet/schema.json](sheet/schema.json) and returns the link. Save the sheet ID in `private/profile.md`.
4. **Schedule the scan.** Fill in the placeholders in [prompts/daily-scan.md](prompts/daily-scan.md) and run it once a day: a Claude Code routine, cron, or Muse's scheduler.
5. **Build your base resume** from [resume/template.tex](resume/template.tex) and compile it with [Tectonic](https://tectonic-typesetting.github.io/): `tectonic resume.tex`.
6. **Optional:** pair it with [career-ops](https://github.com/santifer/career-ops) for portal scanning, job evaluation and interview tooling.

## Prompts

| File | Use it to |
|---|---|
| [create-sheet.md](prompts/create-sheet.md) | Build the tracking sheet from the schema |
| [daily-scan.md](prompts/daily-scan.md) | Run the scheduled daily scan |
| [linkedin-search.md](prompts/linkedin-search.md) | Write Boolean people searches for a job |
| [network-scoring.md](prompts/network-scoring.md) | Score your LinkedIn connections export |
| [outreach.md](prompts/outreach.md) | Draft the right message for a recruiter, hiring manager or peer |
| [tailor-resume.md](prompts/tailor-resume.md) | Tailor the resume and cover letter to one job |
| [apply.md](prompts/apply.md) | Submit an application and log it |
| [interview-prep.md](prompts/interview-prep.md) | Prepare for a screen or a loop |

## Scripts

- `scripts/build_sheet_requests.py`: turns `sheet/schema.json` into one Google Sheets `batchUpdate`, so agents never hand-type formatting requests.
- `scripts/linkedin_search.py`: builds the LinkedIn search cells, with a clickable link on each line.
- `scripts/check_pdf.py`: checks a compiled resume: one page, no fused ligatures that break ATS keyword matching, and no lines that wrap with 1–3 orphan words.

## Credits

- [career-ops](https://github.com/santifer/career-ops) by Santiago Fernández de Valderrama (MIT): the scanning and evaluation engine this sits beside.
- [Jake's Resume](https://github.com/jakegut/resume) (MIT): the LaTeX layout.
- Resume advice from [Diego Granados](https://www.linkedin.com/in/diegogranadosa/): no generic skills list; graduation year only.
- Networking method from Mikelle's [UNLISTED](https://mikellecareers.com) networking guide: mine your warm network first, then go cold with Boolean search and a message matched to the reader.

## License

MIT
