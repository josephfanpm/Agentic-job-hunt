# How to use agentic-job-hunt

This guide takes you from cloning the repo to sending your first applications. Plan on about an hour for setup. After that, the daily routine takes 20–30 minutes.

## What you need

| Tool | Why | Required? |
|---|---|---|
| [Claude Code](https://claude.com/claude-code) | The main agent: it builds the sheet, scans, tailors, applies and preps interviews | Yes, or another agent that can do the same |
| Google Sheets connector | Lets the agents read and write your tracking sheet | Yes |
| Python 3.10+ | Runs the scripts (`pip install pymupdf python-jobspy`) | Yes |
| [Tectonic](https://tectonic-typesetting.github.io/) | Compiles LaTeX resumes into PDFs, with no full LaTeX install needed | Yes, for resumes |
| Muse or another apply agent | A second agent working the same sheet in parallel | Optional |
| LinkedIn Premium | Shows 2nd vs 3rd degree connections and raises search limits | Optional, but useful while you're searching |

Any agent can work in this system if it can read the files in this repo and edit a Google Sheet. [AGENTS.md](AGENTS.md) is the contract every agent follows.

---

## Part 1: One-time setup

### Step 1. Clone and create your private folder

```bash
git clone https://github.com/josephfanpm/agentic-job-hunt.git
cd agentic-job-hunt
mkdir private
cp examples/profile.example.md private/profile.md
```

`private/` is git-ignored. Your resume, contacts, sheet ID and LinkedIn export live there and never get committed.

### Step 2. Fill in your profile

Open `private/profile.md` and fill in every section. This is the most important step: **agents use only facts written here**. If a win, metric or tool isn't in this file, the agents won't use it.

Tips:
- Under **Wins and metrics**, write one line per result with its number and where the number comes from. If you couldn't defend a number in an interview, leave it out.
- Under **Approved bullets**, paste resume bullets you've already signed off on. Agents use them word for word.
- Under **Priority companies**, list companies where someone has agreed to refer you. The scan puts their jobs at the top.

### Step 3. Create your tracking sheet

Open Claude Code in the repo folder and say:

> Run prompts/create-sheet.md

The agent creates a Google Sheet with three tabs:

- **Daily jobs:** new roles from the scan. You tick **Applied** when you apply.
- **Applied:** every application, with Status, follow-up date and Channel (Referral, Hiring manager message, Cold application or Auto-apply).
- **Network:** people to contact, with draft messages, status, and a follow-up date that fills itself in 7 days after you message someone.

The agent saves the sheet ID to your profile and gives you the link.

### Step 4. Build your base resume

Copy `resume/template.tex` to `private/resume.tex` and fill it in yourself, or ask:

> Build my base resume in private/resume.tex from private/profile.md, following prompts/tailor-resume.md

Then compile and check it:

```bash
tectonic private/resume.tex
python scripts/check_pdf.py private/resume.pdf
```

The checker fails if the PDF runs past one page, if letters got fused in a way that breaks keyword matching ("staffing" read as "sta?ing"), or if a line wraps with only 1–3 words on it.

### Step 5. Mine your LinkedIn network

Request your data from LinkedIn: **Settings & Privacy → Data privacy → Download your data → larger archive**. It takes about 30 minutes. Put `Connections.csv` and `messages.csv` in `private/`, then say:

> Run prompts/network-scoring.md. My goal is [your goal].

You get the 4s and 5s out of every connection, sorted into categories, each with a reason and an opener. They're written to the Network tab. The agent also tells you which groups are missing from your network, which is where you'll search for new people.

### Step 6. Schedule the daily scan

Open [prompts/daily-scan.md](prompts/daily-scan.md) and replace every `{{PLACEHOLDER}}`: your searches, target levels, sectors, pay floor and sheet ID. Then schedule it to run once a day. In Claude Code:

> /schedule: run the daily scan in prompts/daily-scan.md every weekday at 8am

Or use cron, Windows Task Scheduler, or Muse's own scheduler. Each morning, new roles appear at the top of Daily jobs, ranked, each with three LinkedIn people searches.

---

## Part 2: The daily routine (20–30 minutes)

1. **Open the sheet.** Read today's new rows. Each has a rank, pay, a one-line reason it fits, and a link.
2. **Pick 2–5 jobs.** Ignore the rest. Picking a few strong fits beats mass-applying.
3. **Find a person.** Click the jobs' **LinkedIn search** links. Set LinkedIn's *Current company* filter, then pick one recruiter, hiring manager or peer per job.
4. **Hand the jobs to an agent:**
   > Tailor and apply to rows 3 and 5 in Daily jobs. Draft a message to [name, title] for each.

   For each job, the agent:
   - fetches the real job description
   - tailors a one-page resume and a cover letter if the form takes one
   - runs the PDF check
   - checks whether you have a referral path, and asks you before applying if you do
   - fills in the form
   - logs the application in the Applied tab
   - drafts the message
5. **Answer what it asks.** Agents stop and ask before sponsorship or work-authorization questions, and before applying when a referral is possible.
6. **Send the messages yourself.** Agents never send under your name.
7. **Follow up.** When a Follow up on date arrives, send one short nudge, then let it go.

### When you have a referral

Ask the referrer **before** you apply. Most companies want the referrer to submit you first, with the same email you'll apply with. If you've already applied, they can still flag you to the recruiter directly. Send them the job ID and your tailored resume.

### When an interview comes in

> Run prompts/interview-prep.md for [company, role]. The job description is row 7.

You get stories matched to the role, practice questions, and questions to ask them. Keep each answer to about 90 seconds and lead with the result.

---

## Part 3: Weekly review (15 minutes)

- **Network:** draft 5 new messages from the Network tab:
  > Draft this week's 5 network messages following prompts/outreach.md
- **Channels:** after about 3 weeks, count interviews by Channel in the Applied tab, and spend more time on whichever channel gets screens. For most people it's referrals.
- **Statuses:** update the Applied rows that are stuck, and mark No response after 3 weeks of silence.

---

## Running two agents at once

Claude and Muse (or any two agents) can share one sheet safely, because both follow [AGENTS.md](AGENTS.md):

- New rows are inserted under the header. Agents never reorder, delete or overwrite each other's rows.
- Before working on a job, an agent claims it in the Notes column (`Claude 2026-11-15: tailoring`), and the other agent skips it.
- Both agents dedupe on Company + Role across the Daily jobs and Applied tabs.
- Each column has an owner in `sheet/schema.json`: the scan, any agent, or only you.

A simple split: one agent runs the daily scan and tailors, and the other applies through job-site logins. Either one can do everything alone.

---

## Customizing

| To change | Edit |
|---|---|
| Which jobs the scan finds | The searches, levels and sectors in your copy of `prompts/daily-scan.md` |
| Columns in the sheet | `sheet/schema.json`, then ask an agent to add the new column to your live sheet |
| Resume look | `resume/template.tex` (keep the `fontspec` line with `Ligatures=NoCommon`) |
| Message style | `prompts/outreach.md` |
| A function other than product | The hiring manager titles in `prompts/linkedin-search.md` and the levels in the scan |

---

## FAQ

**Will it apply to jobs without asking me?** Only to jobs you pick. The scan just lists roles. Agents also stop and ask about referrals and sponsorship questions.

**Will it make up experience?** No. Every rule says to use only facts in `private/profile.md` and your own files. Before you send a resume, read it once anyway; you're the last check.

**Does my data leave my machine?** Your files in `private/` stay local and git-ignored. The tracking sheet is in your own Google Drive. The agents send text to their model providers to do the work, as any AI tool does.

**LinkedIn search shows people who left the company.** Keyword search matches past jobs too. Set the *Current company* filter after the search opens.

**A captcha or login blocked the agent.** It hands that job back to you. Agents never try to get around captchas.

**Do I need career-ops?** No. [career-ops](https://github.com/santifer/career-ops) adds company job-portal scanning, job scoring and interview tools, and it works alongside this repo.
