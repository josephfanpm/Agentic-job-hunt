# agentic-job-hunt

A job search run by scripts, AI agents and one human. Scripts find and rank the jobs. Agents tailor resumes, draft outreach and prepare applications. You pick the jobs, send the messages and do the interviews.

It works for any role: set your job titles in one config file. You choose how much the AI does, from almost nothing to nearly everything.

```bash
git clone https://github.com/josephfanpm/agentic-job-hunt.git && cd agentic-job-hunt
pip install -r requirements.txt
python -m jobhunt init --resume path/to/your-resume.pdf    # asks a few questions
python -m jobhunt scan                                     # today's ranked jobs
```

## What it does

| Stage | What happens | Needs AI? |
|---|---|---|
| **Set up** | One command drafts your profile from your resume, finds your target companies' job boards, and creates the tracker | No |
| **Scan** | Reads company job boards (Greenhouse, Lever, Ashby, Workable), remote boards (Remote OK, Remotive, We Work Remotely, Himalayas), Hacker News "Who is hiring?", Amazon, and optionally LinkedIn and Indeed. Filters, ranks and removes duplicates | No |
| **Find people** | Three LinkedIn searches per job (recruiters, hiring managers, peers), each a one-click link | No |
| **Check the resume** | Reads your PDF the way an applicant tracking system does, and shows which of the posting's terms your resume lacks | No |
| **Track** | Logs applications, lists follow-ups due, compares interview rates by channel | No |
| **Evaluate and research** | Grades a job's fit against your profile; writes a one-page company brief | Yes |
| **Tailor** | A one-page LaTeX resume and cover letter per job, from the real job description and your own facts | Yes |
| **Reach out** | A message matched to who's reading it. Agents draft; **you send** | Yes |
| **Apply** | Fills the application and logs it. Stops for referrals and sponsorship questions | Yes |
| **Interview** | A story bank, a mock interview with a tough-interviewer setting, and a debrief | Yes |
| **Offer** | Side-by-side comparison and a negotiation draft | Yes |

## Choose your flow

| Flow | The AI does | Pick it if |
|---|---|---|
| **Lean** | Only what you ask, for jobs you pick | You want the lowest AI usage |
| **Standard** | Reviews the scan, tailors and drafts for jobs you pick | You want a balance |
| **Full** | Evaluates every new job and prepares applications ahead | You want the least work |

```bash
python -m jobhunt mode lean      # or standard, full
```

In Lean mode with the CSV tracker, the daily scan uses no AI at all. [MODES.md](MODES.md) has the full comparison.

## Commands

| Command | Does |
|---|---|
| `python -m jobhunt init` | Set up your private folder, profile, config and tracker |
| `python -m jobhunt scan` | Find, filter and rank new jobs (`--dry-run` to preview) |
| `python -m jobhunt boards add "Company"` | Find and track a company's job board |
| `python -m jobhunt people "Company" "Job title"` | LinkedIn searches for recruiters, hiring managers and peers |
| `python -m jobhunt check resume.pdf --jd job.txt` | Resume pre-flight and keyword gap |
| `python -m jobhunt applied "Company" --channel Referral` | Log an application |
| `python -m jobhunt due` | Follow-ups due today |
| `python -m jobhunt stats` | Interviews by channel |
| `python -m jobhunt mode` | Show or change the flow |
| `python -m jobhunt doctor` | Check the setup |

## Works with more than one agent

Claude and Muse (or any two agents) can share one tracker: both can create the Google Sheet, run the scan, tailor and apply. They follow one contract ([AGENTS.md](AGENTS.md)), so they never overwrite each other's work. Any agent that can run a command and edit a sheet can join.

## The rules that make it work

- **You pick, agents execute.** The scan gives you a short ranked list. You choose; agents do the rest.
- **Referral before application.** Line up a referral first where you can. The tracker records the channel for every application, so you can see which one gets interviews.
- **Message a person for every application.**
- **Never invent anything.** Agents tailor only from a job description they fetched and facts in your own files. Pay, dates and locations are shown only when the posting states them.
- **Agents draft, you send.**
- **Your data stays yours.** Everything personal lives in `private/`, which is never committed.

## Guides

- **[GUIDE.md](GUIDE.md):** setup, the daily routine, the weekly review
- **[MODES.md](MODES.md):** the three flows and what each costs
- **[AGENTS.md](AGENTS.md):** the contract every agent follows
- **Prompts:**
  - Finding: [daily-scan](prompts/daily-scan.md), [evaluate](prompts/evaluate.md), [research](prompts/research.md)
  - People: [network-scoring](prompts/network-scoring.md), [linkedin-search](prompts/linkedin-search.md), [outreach](prompts/outreach.md), [follow-up](prompts/follow-up.md)
  - Applying: [tailor-resume](prompts/tailor-resume.md), [apply](prompts/apply.md), [create-sheet](prompts/create-sheet.md)
  - Interviews and offers: [interview-prep](prompts/interview-prep.md), [mock-interview](prompts/mock-interview.md), [offer](prompts/offer.md), [review](prompts/review.md)

## Development

```bash
pip install -r requirements.txt
python -m pytest -q
```

The scan engine uses only the Python standard library. `pymupdf` is needed for the resume check. Tests run without network access.

## Credits

- [career-ops](https://github.com/santifer/career-ops) by Santiago Fernández de Valderrama (MIT): the project that inspired this workflow.
- [Jake's Resume](https://github.com/jakegut/resume) (MIT): the LaTeX layout.
- Resume advice from [Diego Granados](https://www.linkedin.com/in/diegogranadosa/): no generic skills list; graduation year only.
- Networking method from Mikelle's [UNLISTED](https://mikellecareers.com) networking guide.
- Job data comes from each board's public feed. Listings from Remote OK and Remotive link back to those sites, as their terms ask.

## License

MIT
