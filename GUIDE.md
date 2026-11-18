# How to use agentic-job-hunt

This guide takes you from cloning the repo to sending your first applications. Setup takes about 15 minutes. After that, the daily routine takes 20–30 minutes.

## What you need

| Tool | Why | Required? |
|---|---|---|
| Python 3.10+ | Runs the scan, the resume check and the tracker | Yes |
| An AI agent: [Claude Code](https://claude.com/claude-code), Codex, Antigravity, Grok Build, Muse, or [an open model in your IDE](#using-open-weight-models) | Tailors resumes, drafts messages, applies, runs interview practice | For those steps. The scan and tracker work without one |
| [Tectonic](https://tectonic-typesetting.github.io/) | Turns the LaTeX resume into a PDF, with no full LaTeX install | For tailored resumes |
| Google Sheets connector | Only if you track in a Google Sheet; the default is local CSV files | Optional |
| Gmail connector | Saves messages as Gmail drafts and updates the tracker from replies ([check-email.md](prompts/check-email.md)) | Optional |
| A second agent, such as Muse or Grok | Works the same tracker in parallel | Optional |
| LinkedIn Premium | Shows 2nd vs 3rd degree connections and raises search limits | Optional, useful while searching |

---

## Part 1: One-time setup

### Step 1. Install and run the setup

```bash
git clone https://github.com/josephfanpm/agentic-job-hunt.git
cd agentic-job-hunt
pip install -r requirements.txt
python -m jobhunt init --resume path/to/your-resume.pdf
```

It asks a few questions: the job titles you want, words that rule a title out, topics you want more of, countries you can work in, your pay floor, and companies to watch. Then it:

- creates `private/`, which is never committed and holds everything personal
- drafts `private/profile.md` from your resume: contact details, experience, education and tools
- finds the job boards of the companies you named
- writes `private/config.json`
- creates the tracker

An agent can run setup for you in one line:

```bash
python -m jobhunt init --resume cv.pdf --titles "data analyst, senior data analyst" \
  --exclude "intern,director" --boost "healthcare,sql" --countries US,CA \
  --pay-floor 90000 --priority "Acme" --companies "Globex, Initech"
```

Run `python -m jobhunt doctor` at any time to see what's missing.

Or have your agent do all of Part 1, including the Sheet, Gmail and the profile interview:

> Follow prompts/setup.md

### Step 2. Build your experience bank

Open `private/profile.md`. The sections marked REVIEW were pulled from your resume by a script, so read them once. Then have your agent interview you:

> Run prompts/profile-interview.md

It asks about each job one question at a time: what the company does, your role, and 2–5 projects with the problem, what you did, the result, the number and its source. Answers go in the **Experience bank** section. Tailoring picks different projects for each job from the bank, so you aren't limited to what fit on one resume. Plan on 20–40 minutes; you can stop and pick it up later.

Two sections only you can approve:

- **Wins and metrics:** one line per result, with its number and where the number comes from. If you couldn't defend a number in an interview, leave it out.
- **Approved bullets:** resume bullets you've signed off on. Agents use them word for word.

This file matters most: **agents use only facts written here.**

### Step 3. Choose your flow and tracker

```bash
python -m jobhunt mode lean      # or standard, full
```

- **Lean:** the AI acts only on jobs you pick. Lowest usage.
- **Standard:** the AI also reviews each scan and drafts follow-ups.
- **Full:** the AI evaluates every new job and prepares applications ahead of time.

[MODES.md](MODES.md) compares them. You can switch whenever you like.

The tracker defaults to CSV files in `private/tracker/`, which need no connector. To use a Google Sheet, ask your agent:

> Run prompts/create-sheet.md

It builds the sheet, then sets `"tracker": "sheet"` and the sheet ID in your config. Your agent needs a Google Sheets or Drive connector for this (in most apps: Settings → Connectors). Connect your personal Google account, not a work one.

To keep the tracker current from your inbox, connect Gmail too, then ask the agent to run [prompts/check-email.md](prompts/check-email.md). It saves replies as Gmail drafts and never sends.

Either way you get three tabs:
- **Daily jobs:** new roles from the scan
- **Applied:** every application, with status, follow-up date and channel
- **Network:** people to contact, with drafts and follow-up dates

### Step 4. Run your first scan

```bash
python -m jobhunt scan --dry-run     # preview; records nothing
python -m jobhunt scan               # adds new jobs to your tracker
```

Each job gets a score, pay if the posting states it, and a one-line reason built from your rules. The scan also prints how many jobs each rule dropped. If the list looks wrong, see "Tuning" in [prompts/daily-scan.md](prompts/daily-scan.md).

Add more companies at any time:

```bash
python -m jobhunt boards add "Stripe" "Shopify"
```

### Step 5. Build your base resume

Setup copied your resume to `private/`, or the LaTeX template if you gave none. To build a clean one-page version, ask your agent:

> Build my base resume in private/resume.tex from private/profile.md, following prompts/tailor-resume.md

Then compile and check it:

```bash
tectonic private/resume.tex
python -m jobhunt check private/resume.pdf
```

The check reads the PDF the way an applicant tracking system does. It fails on things that break parsing: more than one page, fused letters ("staffing" read as "sta?ing"), no email in the text, a scanned image with no text. It warns about missing section headings, multi-column layouts and images. It also reads your bullets the way a recruiter skims them, and warns when fewer than 80% carry a number, when a bullet opens with a duty ("Responsible for"), when it uses filler ("team player"), or when a tool on your list never shows up in a bullet. `--bullets` lists each bullet with what it's missing. The README's [Resume rules, and why](README.md#resume-rules-and-why) explains each rule.

Building the base resume for a role? Once the scan has saved five or more job descriptions, run `python -m jobhunt terms private/jds/*.txt` to see the terms that three or more of them share.

### Step 6. Mine your LinkedIn network

Download your LinkedIn data ([the clicks are in START-HERE](START-HERE.md#add-your-linkedin-data-optional); the full archive takes up to 24 hours). Unzip it anywhere, then index it:

```bash
python -m jobhunt network build "<the unzipped folder>"
```

This reads your connections, messages, endorsements, recommendations and invitations into `private/network/`. From then on, before any application:

```bash
python -m jobhunt network find "Company"
```

lists everyone you know there, warmest first (people who replied to you, then people who endorsed or recommended you), plus invitations you sent that they haven't accepted. If a company goes by several names, add them to `linkedin.company_aliases` in your config.

To pick who to reach out to across your whole network, say:

> Run prompts/network-scoring.md. My goal is [your goal].

You get the strongest matches among your connections, each with a reason and an opener, plus the groups missing from your network. Rebuild the index whenever you download a new export.

### Step 7. Schedule the daily scan

```bash
python -m jobhunt schedule on               # at log-on; add --at 08:00 for a set time too
```

The scan then runs on your own computer, at most once a day, with no AI and no window. With a Google Sheet, set up the receiver first ([sheet/README-apps-script.md](sheet/README-apps-script.md), about 5 minutes) so results can reach the sheet.

Prefer this to a scheduled cloud agent. Cloud sandboxes often block job sites, and a scheduled agent shares your AI usage limit; [prompts/daily-scan.md](prompts/daily-scan.md) explains both.

The list stays fresh on its own. Applied jobs move to the Applied tab, and jobs you haven't applied to move to an Archive tab after 14 days (`expire_after_days`). Jobs at your priority companies are kept.

---

## Part 2: The daily routine (20–30 minutes)

1. **Open your tracker,** or the morning email if you turned it on (`"email_digest": true`, Google Sheet only). Read today's new jobs. The **Who you know** column shows contacts there, if you've added your LinkedIn data.
2. **Tick Pick on 2–5 jobs.** Ignore the rest. A few strong fits beat mass-applying. `python -m jobhunt picks` lists what you've ticked.
3. **Find a person.** First run `python -m jobhunt network find "Company"`: someone you already know there beats any stranger. If nobody turns up, each job has three LinkedIn search links: recruiters, hiring managers and peers. Open one, set LinkedIn's *Current company* filter, and pick someone. For any other company: `python -m jobhunt people "Company" "Job title"`.
4. **See the gap** before tailoring: `python -m jobhunt check private/resume.pdf --jd "private/jds/<Company>__<Title>.txt"`. The scan saved each job description there.
5. **Tell your agent "work my picks"** ([prompts/work-picks.md](prompts/work-picks.md)). For each picked job, the agent:
   - reads the saved job description
   - tailors a one-page resume, and a cover letter if the form takes one
   - runs the resume check
   - checks whether you have a referral path, and asks you before applying if you do
   - fills in the form
   - logs the application
   - drafts the message
6. **Answer what it asks.** Agents stop before sponsorship questions, and before applying where a referral is possible.
7. **Send the messages yourself.** Agents never send under your name.

   > **Get to know a team member before you ask for anything.** When you reach out to someone on the team you're applying to, don't open with the job, your resume or a referral request. Start with an interesting question about their work, a point about something they've built or said, or something you have in common, and suggest a short coffee chat. Ask about the role, or for a referral, only after you've talked. A first message that asks for something reads as transactional; a good question starts a conversation.

8. **Log anything you did by hand:** `python -m jobhunt applied "Company" --channel Referral`.
9. **Follow up:** `python -m jobhunt due` lists what's due. Send one short nudge ([prompts/follow-up.md](prompts/follow-up.md)), then let it go.

### When you have a referral

Ask the referrer **before** you apply. Most companies want the referrer to submit you first, with the same email you'll apply with. If you've already applied, they can still flag you to the recruiter. Send them the job ID and your tailored resume.

### Before you apply to a stretch role

> Run prompts/evaluate.md on the Acme job.

You get a grade, the evidence from your profile, the gaps, and one next step.

### When an interview comes in

> Run prompts/research.md for Acme, then prompts/mock-interview.md for the hiring manager round, tough mode.

The mock interview asks one question at a time from the real job description and your resume, then gives a debrief with your two weakest answers rewritten. Keep answers to about 90 seconds and lead with the result.

### When an offer comes in

> Run prompts/offer.md with these two offers.

---

## Part 3: Weekly review (15 minutes)

- **Network:** draft 5 new messages:
  > Draft this week's 5 network messages following prompts/outreach.md
- **Channels:** `python -m jobhunt stats` shows interviews per channel. With fewer than about 20 applications it's too early to compare; after that, put your time where the screens come from.
- **Statuses:** update the Applied rows that are stuck, and mark "No response" after 3 weeks of silence.
- **Deeper review:** [prompts/review.md](prompts/review.md).

---

## Running two agents at once

To start any agent (Muse, Grok, Codex or another) on the whole job search, paste the kickoff message from [prompts/kickoff.md](prompts/kickoff.md). It has one version for agents that can run commands and one for chat-only sites such as grok.com.

Claude and Muse, Grok, or any two agents can share one tracker safely, because both follow [AGENTS.md](AGENTS.md):

- New rows are inserted under the header. Agents never reorder, delete or overwrite each other's rows.
- Before working on a job, an agent claims it in the Notes column, and the other agent skips it.
- The scan remembers every job it has shown, so nothing is listed twice.
- Each column has an owner in `sheet/schema.json`: the scan, any agent, or only you.

A simple split: one agent tailors, the other applies through job-site logins. Either can do everything alone.

---

## Using open-weight models

Any agent that can run shell commands, edit files and read `AGENTS.md` works, including ones running open-weight models.

**In VS Code (or Cursor, Windsurf, VSCodium):** install [Cline](https://cline.bot), Roo Code or [Continue](https://continue.dev), open the project folder, and pick a provider in the extension's settings:

| Provider | What it is | Notes |
|---|---|---|
| [DeepSeek](https://platform.deepseek.com) | DeepSeek's own API | Very cheap per token. Data is stored in China |
| [OpenRouter](https://openrouter.ai) | One key for many open models (DeepSeek, Qwen, Kimi, GLM and others) | Some models are free with a daily cap. Free ones can queue at busy times |
| [xAI](https://x.ai/api) | Grok models through an API key | Paid per token. Grok Build is the native app |
| [Ollama](https://ollama.com) or [LM Studio](https://lmstudio.ai) | Runs the model on your computer | Free and private. Needs a lot of memory (see below) |

**In a terminal:** [OpenCode](https://opencode.ai) and [Aider](https://aider.chat) work with the same providers. Start one in the project folder and tell it: *Read AGENTS.md, then follow prompts/setup.md* (or the kickoff message in [prompts/kickoff.md](prompts/kickoff.md)).

**What the model needs:**
- **Reliable tool calling.** The agent has to run `python -m jobhunt …` and edit files over many steps. Small models often lose track and stop, or invent output.
- **A long context window,** at least 32k tokens. `AGENTS.md`, the profile, a job description and the resume template add up. Ollama's default context is much smaller, so raise it (`num_ctx`) or the model will quietly drop your profile.
- **For local models,** a coding model of about 30B parameters or more, which needs roughly 24 GB of free RAM or VRAM. 7–14B models can run the scan but are unreliable at tailoring.

Whatever the model, run `python -m jobhunt check` on every resume and read it yourself before sending. The never-invent rules in `AGENTS.md` only hold as well as the model follows them.

---

## Customizing

Everything is in `private/config.json`. [examples/config.example.json](examples/config.example.json) shows every setting.

| To change | Edit |
|---|---|
| Which jobs the scan finds | `titles`, `keywords`, `locations`, `max_age_days` |
| Where it looks | `companies` (or `boards add`) and `sources` |
| How jobs rank | `keywords.boost`, `priority_companies`, `pay`, `locations.prefer` |
| The LinkedIn searches | `linkedin.manager_titles` and `linkedin.peer_titles` |
| Columns in the tracker | `sheet/schema.json` |
| Resume look | `resume/template.tex` (keep the `fontspec` line with `Ligatures=NoCommon`) |
| Message style | `prompts/outreach.md` |

---

## FAQ

**Will it apply to jobs without asking me?** No. The scan only lists roles. Agents work on jobs you pick, and stop for referrals and sponsorship questions. In Full mode, agents prepare applications ahead of time, but you still choose what goes out.

**Will it make up experience?** No. Agents use only facts in `private/profile.md` and your own files, and the scan shows pay, dates and locations only when the posting states them. Read every resume once before you send it; you're the last check.

**How much AI does it use?** That depends on the flow. In Lean mode with the CSV tracker, a day when you apply to nothing uses none. See [MODES.md](MODES.md).

**Does it work for roles other than product management?** Yes. Titles, keywords and locations are settings. The LinkedIn searches work out likely manager titles for common roles (engineer, designer, analyst, scientist, manager); for others, set `linkedin.manager_titles` yourself.

**Does my data leave my machine?** Files in `private/` stay local. The scan sends only ordinary requests for public job listings. A Google Sheet lives in your own Drive. Agents send text to their model providers to do their work, as any AI tool does.

**A company isn't found by `boards add`.** It may use a system without a public feed, such as Workday. Its roles can still arrive through the other sources.

**The keyword gap lists odd words.** It's a counting heuristic over the posting's text, not a judgment. Use it as a prompt for what to check, and add a term only where you have real experience behind it.

**LinkedIn search shows people who left the company.** Keyword search matches past jobs too. Set the *Current company* filter after the search opens.

**A captcha or login blocked the agent.** It hands that job back to you. Agents never try to get around captchas.
