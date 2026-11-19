# agentic-job-hunt

A job search run by scripts, AI agents and one human. Scripts find and rank the jobs. Agents tailor resumes, draft outreach and prepare applications. You pick the jobs, send the messages and do the interviews.

It works for any role: set your job titles in one config file. You choose how much the AI does, from almost nothing to nearly everything.

**Full mode can apply by itself.** Turn on auto-apply, and the agent grades each new job, tailors a resume for the best matches, submits the applications, and names the person to message at each company. All that's left for you is sending the messages. It's off until you switch it on: see [Auto-apply](#auto-apply).

## Get started

### Option 1: let an AI agent set it up (about 10 minutes)

This works whether or not you code. The agent installs what's missing, asks about your search, builds your tracker, interviews you about your experience, and runs the first scan.

- **You already use an agent** (Claude Code, Codex, Antigravity, Grok Build, Cline): open an empty folder with your resume in it and say *"Set up https://github.com/josephfanpm/agentic-job-hunt in this folder by following prompts/setup.md."*
- **You don't, or you've never used a terminal:** [START-HERE.md](START-HERE.md) shows which free app to install and the exact message to paste. No paid plan or code editor needed.

### Option 2: do it yourself

- **Not a programmer:** follow Steps 1 to 5 in [START-HERE.md](START-HERE.md). Every click is written out.
- **Developer:**

  ```bash
  git clone https://github.com/josephfanpm/agentic-job-hunt.git && cd agentic-job-hunt
  pip install -r requirements.txt
  python -m jobhunt init --resume path/to/your-resume.pdf    # asks a few questions
  python -m jobhunt scan                                     # today's ranked jobs
  ```

  Then continue with [GUIDE.md](GUIDE.md) from Step 2.

After setup, everyone uses [GUIDE.md](GUIDE.md) for the daily routine.

## What it does

| Stage | What happens | Needs AI? |
|---|---|---|
| **Set up** | One command drafts your profile from your resume, finds your target companies' job boards, and creates the tracker | No |
| **Scan** | Reads company job boards (Greenhouse, Lever, Ashby, Workable, Workday), remote boards (Remote OK, Remotive, We Work Remotely, Himalayas), Hacker News "Who is hiring?", Amazon, and optionally LinkedIn and Indeed. Filters, ranks and removes duplicates | No |
| **Pick** | Tick Pick on the jobs you want, in the sheet, on your phone, or from a morning email. Then tell your agent "work my picks" | No |
| **Find people** | Three LinkedIn searches per job (recruiters, hiring managers, peers), each a one-click link | No |
| **Check the resume** | Reads your PDF the way an applicant tracking system does, shows which of the posting's terms your resume lacks, and flags bullets with no number, duty openers, filler, and tools no bullet shows | No |
| **Track** | Logs applications, lists follow-ups due, compares interview rates by channel | No |
| **Evaluate and research** | Grades a job's fit against your profile; writes a one-page company brief | Yes |
| **Tailor** | A one-page LaTeX resume and cover letter per job, from the real job description and your own facts | Yes |
| **Reach out** | A message matched to who's reading it. Team members get a question or a shared interest and a coffee-chat invite, not a request. Agents draft; **you send** | Yes |
| **Apply** | Fills the application and logs it, for jobs you pick. With auto-apply on in Full mode, it also submits for the top matches without asking. Stops for referrals and for questions your profile doesn't answer | Yes |
| **Name the person** | In Full mode, the agent names one person to message per job: the hiring manager, a recruiter, or a manager who could be hiring for the role | Yes |
| **Interview** | A story bank, a mock interview with a tough-interviewer setting, and a debrief | Yes |
| **Offer** | Side-by-side comparison and a negotiation draft | Yes |

## Why it works this way

### Cold applications rarely work anymore

- **Each opening gets flooded.** Employers on Greenhouse received about 194 applications per hire in late 2026. On Ashby it was about 291.[^gh][^ashby-in]
- **Few cold applicants get through.** On Ashby, people who applied cold got an interview 3% of the time and an offer 0.2% of the time.[^ashby-ref]
- **Volume keeps rising.** LinkedIn receives about 11,000 applications a minute. At small businesses, the share of applicants who get an interview fell from 15% in 2016 to 3% in 2024.[^li][^cp]
- **AI-written applications all look alike.** After an AI cover-letter tool launched, a well-matched cover letter stopped predicting who got a callback. Employers leaned on work history instead.[^cui]
- **Some postings aren't real.** An estimated 18–26% are "ghost jobs" that may never be filled.[^ghost]

Sending more applications doesn't fix low odds per application. It also uses the time that would go into what does work.

### What works now

- **Referrals.** On Ashby, referred candidates got an interview 40% of the time and an offer 7.3% of the time: about 36 times the cold rate. Referrals were about 1% of applications but about 18% of hires.[^ashby-ref]
- **Being found by a company's recruiter.** Candidates a recruiter reaches out to are hired about 8 times as often as cold applicants. Referrals are hired about 11 times as often.[^gem]
- **Acquaintances, not only close friends.** A randomized study of 20 million LinkedIn users found people you know moderately well lead to more job moves than close friends.[^weak]
- **Tailoring.** Tailored resumes converted about 1.6 times as often in one tracker's user data. A field study of about 500,000 job seekers found better-written resumes raised hiring by 8%.[^huntr][^resume]
- **Applying early.** Most applications arrive in a posting's first week, and people apply more when few others have.[^ashby-in][^bu]

### The flow, and where each best practice fits

| Step | What the tool does | Best practice it applies |
|---|---|---|
| **1. Scan** | Checks company job boards every day and ranks what's new. Old jobs move to an archive after 14 days | **Apply early.** You see a job within a day of its posting, while you're among the first applicants |
| **2. Pick** | You tick **Pick** on 2–5 jobs: in the sheet, on your phone, or from the morning email | **Fit over volume.** Your time goes to a few strong fits, where a referral and tailoring pay off |
| **3. Check who you know** | **Who you know** shows contacts at each company, from your LinkedIn data. `network find` lists them | **Referral first.** The single biggest factor in the data: about 36 times the offer rate of applying cold |
| **4. Find the right person** | Three LinkedIn searches per job: recruiters, hiring managers and peers | **Reach a person, not a pile.** A direct message turns a cold application into a conversation |
| **5. Tailor** | A resume per job, built from your own record of real work and checked to make sure it reads correctly | **Tailoring and specifics.** Specific, true detail stands out where generic AI text doesn't |
| **6. Apply** | An agent fills in the form for jobs *you* picked. With auto-apply on, it also submits for the top-graded matches, up to a daily limit. It stops when a referral is possible and for questions your profile doesn't answer | **No mass-applying.** The odds of a cold application are too low to make volume worth it, so auto-apply is limited to strong fits and a few a day |
| **7. Reach out** | Drafts a short message matched to the reader. For a team member: an interesting question, a point about their work, or something you share, plus a coffee-chat invite. **You send it** | **Relationship before the ask.** A message sent by you, with a real detail and no request, starts a conversation; the referral comes after |
| **8. Follow up and measure** | Lists follow-ups due, and compares interview rates by channel: referral, hiring-manager message, cold | **Do more of what works.** Your own numbers show where to spend next week's time |

> **Get to know a team member before you ask for anything.** When you reach out to someone on the team you're applying to, don't open with the job, your resume or a referral request. Start with an interesting question about their work, a point about something they've built or said, or something you have in common, and suggest a short coffee chat. Ask about the role, or for a referral, only after you've talked. A first message that asks for something reads as transactional; a good question starts a conversation.

### Resume rules, and why

Every tailored resume follows these rules ([prompts/tailor-resume.md](prompts/tailor-resume.md)). `python -m jobhunt check` tests the ones marked ✓, so you don't have to remember them.

| Rule | Why it's the best choice | Checked |
|---|---|---|
| **Put the strongest match in the top third.** The first role's title and first 2–3 bullets should answer "does this person fit?" | Recruiters skim before they read. An eye-tracking study clocked the first pass at about 7 seconds, spent mostly on job titles and headings.[^ladders] What isn't near the top may never be seen | ✓ with `--jd`: which of the posting's terms sit in the top third |
| **Each bullet: action, what you did with which tool or method, and the result.** | A duty says what you were supposed to do; a result says what happened because of you. Naming the tool shows how you got there, which is the evidence a hiring manager checks in the interview | |
| **A number in most bullets (aim for 80%), but only numbers you can source.** | A number lets a stranger judge the size of the work: "cut costs" could mean anything, "cut costs 20%" can't. But a number you can't defend in an interview costs more trust than it earns, so the tool never estimates one | ✓ share of bullets with a number |
| **Open with a strong verb, never a duty.** "Launched", "Cut", "Grew", not "Responsible for", "Helped" or "Worked on" | The first word is what a skimming eye catches. A duty opener hides your part in the work | ✓ duty openers |
| **No filler.** No "team player", "various", "results-driven" | Recruiters can't check these, and every applicant writes them, so they take space without telling the reader anything | ✓ common filler |
| **No generic skills list. Show keywords inside bullets; keep a short Tools line.** | A listed skill is a claim; a bullet that shows what you did with it is evidence. The Tools line stays because recruiters search their tracking system by tool name | ✓ tools on the list that no bullet shows |
| **Mirror the job description's words, only where they're true.** For the base resume, use the terms that appear in 3+ postings for the role (`python -m jobhunt terms`) | Recruiters search and skim for the posting's own words. If you did the same work under a different name, using their name makes the match visible. Terms shared by several postings describe the role itself, not one company's quirks | ✓ keyword gap |
| **Tailor every resume from the real posting.** Different jobs get different projects in a different order | Tailored resumes converted about 1.6 times as often, and better-written resumes raised hiring by 8%.[^huntr][^resume] A resume written from a guessed posting tailors to the wrong job | |
| **Plain language.** No internal feature names | The recruiter doesn't work at your company. If they can't picture what changed, the result doesn't count | |
| **No summary or objective, unless you're changing careers.** | The top of the page is the most-read space. Give it to your strongest evidence. A two-line summary only helps when your experience alone doesn't explain why you fit | |
| **Projects only when they match the job.** | An unrelated project takes space from experience that does match. A matching one fills a gap your jobs don't cover | |
| **Graduation year only.** | The year places you on a timeline without months to scan. Leave it off if you'd rather not invite guesses about your age | |
| **One page, one column, real text, no fused letters.** | Tracking systems read text in stored order. Two columns scramble it, text inside images is invisible, and fused letters turn "staffing" into "sta?ing", so the keyword never matches | ✓ fails the check |

### Where the evidence is thin

- **How many jobs to pick a day.** No study shows that fewer applications do better. "2–5" is about where your time goes, not a proven number.
- **The resume check.** There's no good evidence that tracking software rejects resumes for missing keywords. Treat the keyword report as a gap finder, not a way to beat the software.
- **Resume length.** One tracker's data shows two-page resumes did as well or better. One page stays the default because it's quicker to read, not because the data demands it.
- **Follow-up timing.** We found no reliable data on when to follow up. Seven days is a sensible default.
- **The skim time.** The "7 seconds" figure comes from one study by a job site, which didn't publish how many recruiters took part. The point that holds is that the first pass is short and lands on titles and the top of the page; the exact seconds don't.
- **The 80% target for numbers.** It's a common rule of thumb, not a tested threshold. The check warns below it so you look again, not so you add numbers you can't back up.

[^gh]: Greenhouse, *Hire Standard* (2026). https://greenhouse.com/recruiting-benchmarks
[^ashby-in]: Ashby, *Talent Trends: Inbound* (2025). https://www.ashbyhq.com/talent-trends-report/reports/inbound
[^ashby-ref]: Ashby, *Talent Trends: Referrals* (2025), 38M applications. https://www.ashbyhq.com/talent-trends-report/reports/referrals
[^li]: eWeek on LinkedIn application volume (2025). https://www.eweek.com/news/ai-job-applications-linkedin/
[^cp]: CareerPlug, recruiting metrics (2025). https://www.careerplug.com/recruiting-metrics-and-kpis/
[^cui]: Cui, Dias & Ye, field data on AI-written applications (2025). https://arxiv.org/abs/2509.25054
[^ghost]: Greenhouse figure via Entrepreneur (2024); Northwestern and others via CPA Practice Advisor (2025). https://www.entrepreneur.com/business-news/ghost-job-listings-on-the-rise-how-to-spot-avoid-experts/485494 · https://www.cpapracticeadvisor.com/2025/11/12/ghost-jobs-up-to-1-in-3-job-listings-dont-result-in-hires/173044/
[^gem]: Gem, *2026 Recruiting Benchmarks*, 165M applications. https://app.gem.com/blog/key-takeaways-from-the-2026-recruiting-benchmarks-report
[^weak]: Rajkumar et al., *Science* (2022). https://ide.mit.edu/insights/new-publication-mit-harvard-and-stanford-scientists-show-weaker-ties-are-more-beneficial-for-job-seekers-on-linkedin/
[^huntr]: Huntr, *2025 Job Search Trends* (self-reported tracker data). https://huntr.co/research/2025-annual-job-search-trends-report
[^resume]: van Inwegen, Munyikwa & Horton (2023). https://arxiv.org/abs/2301.08083
[^bu]: Fradkin, Boston University (2025). https://www.bu.edu/articles/2025/looking-for-jobs-on-indeed-or-linkedin
[^ladders]: Ladders eye-tracking study (2018), via HR Dive. https://www.hrdive.com/news/eye-tracking-study-shows-recruiters-look-at-resumes-for-7-seconds/541582/

## Choose your flow

| Flow | The AI does | Pick it if |
|---|---|---|
| **Lean** | Only what you ask, for jobs you pick | You want the lowest AI usage |
| **Standard** | Reviews the scan, tailors and drafts for jobs you pick | You want a balance |
| **Full** | Evaluates every new job, prepares applications ahead, and names the person to message. With auto-apply on, it submits them too | You want the least work |

```bash
python -m jobhunt mode lean      # or standard, full
```

In Lean mode with the CSV tracker, the daily scan uses no AI at all. [MODES.md](MODES.md) has the full comparison.

### Auto-apply

```bash
python -m jobhunt mode full --auto-apply       # turn it on
python -m jobhunt mode full --no-auto-apply    # back to: agents prepare, you submit
```

With auto-apply on, your agent works through each day's new jobs by itself:

1. **Grades every new job** against your profile, from the real job description.
2. **Tailors a resume** (and a cover letter, if the form takes one) for jobs graded B or better, and runs the resume check.
3. **Fills in and submits the application**, up to 5 a day. It saves the answers it entered to `private/applications/` first.
4. **Names one person to message:** the hiring manager, then a recruiter. If it finds neither, it picks a manager in the same function who could be hiring for the role, and labels them "not confirmed".
5. **Drafts the message** and logs the application.

Then it gives you a list of messages to send. Sending them is the one step left to you.

It still stops and hands a job back to you when:

- you know someone at the company (ask for a referral first)
- the form asks something your profile doesn't answer, such as a sponsorship question
- the site needs an account, a password, a captcha or an assessment

To fill in forms, the agent needs a tool that can drive a browser. To find people, it uses the posting, the company's site and a web search. It opens LinkedIn only if you set `linkedin.browse` to `true`, and then only in your own signed-in browser, a few pages a day. LinkedIn's terms don't allow automated use, so that setting carries some risk to your account. [MODES.md](MODES.md#auto-apply-full-mode-only) has the settings; [prompts/auto-apply.md](prompts/auto-apply.md) and [prompts/find-person.md](prompts/find-person.md) have the rules agents follow.

## Commands

| Command | Does |
|---|---|
| `python -m jobhunt init` | Set up your private folder, profile, config and tracker |
| `python -m jobhunt scan` | Find, filter and rank new jobs (`--dry-run` to preview) |
| `python -m jobhunt boards add "Company"` | Find and track a company's job board (or pass a Workday careers-page URL) |
| `python -m jobhunt people "Company" "Job title"` | LinkedIn searches for recruiters, hiring managers and peers (`--wider` adds managers on any team and company leaders) |
| `python -m jobhunt picks` | The jobs you ticked Pick and haven't applied to |
| `python -m jobhunt network find "Company"` | Who you already know there, from your LinkedIn data export |
| `python -m jobhunt check resume.pdf --jd job.txt` | Resume pre-flight, bullet checks and keyword gap (`--bullets` lists each bullet and what it's missing) |
| `python -m jobhunt terms private/jds/*.txt` | Terms shared by 3+ postings, for your base resume |
| `python -m jobhunt applied "Company" --channel Referral` | Log an application |
| `python -m jobhunt due` | Follow-ups due today |
| `python -m jobhunt stats` | Interviews by channel |
| `python -m jobhunt mode` | Show or change the flow (`mode full --auto-apply` lets agents submit) |
| `python -m jobhunt schedule on` | Run the scan automatically at log-on (`--at 08:00` for a set time) |
| `python -m jobhunt doctor` | Check the setup |

## Works with more than one agent

Claude, Codex, Antigravity, Grok, Muse, or an open model such as DeepSeek or Qwen in your IDE: any two can share one tracker. Each can create the Google Sheet, run the scan, tailor and apply. They follow one contract ([AGENTS.md](AGENTS.md)), so they never overwrite each other's work. Any agent that can run a command and edit a sheet can join. To start one on the whole search, paste the message in [prompts/kickoff.md](prompts/kickoff.md). Chat-only sites such as grok.com have their own version. GUIDE.md covers [setting up open-weight models](GUIDE.md#using-open-weight-models).

## The rules that make it work

- **You pick, agents execute.** The scan gives you a short ranked list. You choose; agents do the rest. Auto-apply is the one exception, and only when you turn it on: the agent then picks by grade, within a daily limit.
- **Referral before application.** Line up a referral first where you can. The tracker records the channel for every application, so you can see which one gets interviews.
- **Message a person for every application.**
- **Never invent anything.** Agents tailor only from a job description they fetched and facts in your own files. Pay, dates and locations are shown only when the posting states them.
- **Agents draft, you send.**
- **Your data stays yours.** Everything personal lives in `private/`, which is never committed.

## Guides

- **[START-HERE.md](START-HERE.md):** step-by-step setup for non-programmers
- **[GUIDE.md](GUIDE.md):** setup, the daily routine, the weekly review
- **[MODES.md](MODES.md):** the three flows and what each costs
- **[AGENTS.md](AGENTS.md):** the contract every agent follows
- **Prompts:**
  - Getting started: [setup](prompts/setup.md), [profile-interview](prompts/profile-interview.md) (your experience bank), [kickoff](prompts/kickoff.md) (for any agent, including Muse and Grok)
  - Finding: [daily-scan](prompts/daily-scan.md), [evaluate](prompts/evaluate.md), [research](prompts/research.md), [fetch-pages](prompts/fetch-pages.md)
  - Daily: [work-picks](prompts/work-picks.md) (what "work my picks" does), [auto-apply](prompts/auto-apply.md) (Full mode)
  - People: [network-scoring](prompts/network-scoring.md), [linkedin-search](prompts/linkedin-search.md), [find-person](prompts/find-person.md), [outreach](prompts/outreach.md), [follow-up](prompts/follow-up.md), [check-email](prompts/check-email.md)
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
- Job data comes from each board's public feed. Listings from Remote OK and Remotive link back to those sites, as their terms ask.

## License

MIT

---

## Product write-up

*How I approached this as a product problem: who it's for, what I chose not to build, and why.*

### TL;DR

Job seekers spend most of their hours on low-value work: searching boards, reformatting resumes and filling in forms. Meanwhile, the highest-value work gets the least time: referrals, specific outreach, and interview practice. This project moves the low-value work to scripts and AI agents, so the person's time goes where it changes outcomes. The person stays in control of every decision that has their name on it.

**Status:** v0.2, in daily use since November 2026. Open source, MIT licensed.

### The problem

| Who | What hurts today |
|---|---|
| **Active job seekers** | New roles are scattered across dozens of boards and company sites. Checking them by hand takes an hour a day, and the same role shows up three times. |
| | Every application wants a slightly different resume. Tailoring well takes 30–60 minutes per job, so people either skip it or send a generic one. |
| | An applicant tracking system can misread a resume (multi-column layouts, fused letters, text inside images), and the applicant never finds out why they got no reply. |
| | Referrals and messages to the right person get far better responses than cold applications, but finding that person and writing a specific message is slow, so it gets skipped. |
| | Nobody tracks which channel actually produces interviews, so effort never shifts toward what works. |
| **Non-technical job seekers** | AI job tools are either chat windows that forget everything or developer tools that assume a terminal and an IDE. |

**The two failure modes I wanted to avoid:**
1. **Mass-apply bots.** They send hundreds of applications on autopilot. Volume goes up, response rates go down, and accounts get flagged.
2. **Chat-only assistants.** They help with one resume at a time, but they don't find jobs, remember what you applied to, or tell you what's working.

### Goals and non-goals

**Goals**
- Cut the daily search to a short ranked list in seconds, at no AI cost.
- Make a tailored, parser-safe resume and a specific outreach message the default for every application.
- Keep a single record of jobs, applications and contacts that any agent or the person can use.
- Show which channels actually lead to interviews.
- Be usable by someone who has never opened a terminal.

**Non-goals**
- **Applying to as many jobs as possible.** Volume isn't the goal; interviews are. Auto-apply submits only strong fits, a few a day.
- **Sending anything under the user's name without them.** Messages are drafts; the person sends.
- **Writing experience the person doesn't have.** Every claim must trace to the person's own files.
- **Locking users into one AI vendor.**

### Product principles

1. **The person picks; agents execute.** Judgment about *which* job stays human by default. Effort on *how* to apply moves to agents. A person can hand over the picking too, by turning on auto-apply.
2. **Scripts before AI.** Anything a rule can do (search, filter, dedupe, rank, track) is a script: free, fast, repeatable and testable. AI is reserved for writing and judgment.
3. **No invented facts.** Pay, dates and locations appear only when the posting states them. Resume content comes only from the person's profile.
4. **One source of truth, many agents.** A shared tracker and a written contract let several agents work side by side without overwriting each other.
5. **Explain every decision.** Each ranked job carries a plain-language reason, and each scan reports what it filtered out and why.

### How it works

```mermaid
flowchart LR
    A[Job boards and feeds<br/>11 source types] -->|script, no AI| B[Filter, rank, dedupe]
    B --> C[(Tracker<br/>CSV or Google Sheet)]
    C -->|person picks jobs| D{AI agent}
    D --> E[Tailored resume<br/>+ parser check]
    D --> F[Outreach draft]
    D --> G[Application, logged]
    F -->|person sends| H[Recruiter / hiring manager / peer]
    C -->|script| I[Follow-ups due<br/>+ results by channel]
```

### Key decisions and trade-offs

| Decision | Alternative I rejected | Why | What it costs |
|---|---|---|---|
| **Rule-based scan, no AI** | Have an LLM read and score every posting | A scan reads hundreds of postings a day. Rules do it in about 3 seconds, cost nothing, and give the same answer every time | Ranking is cruder than a human read. Standard and Full modes add an AI review on top for people who want it |
| **Three modes: Lean, Standard, Full** | One fixed workflow | AI usage and cost vary a lot by person. Lean uses none on a quiet day; Full prepares applications ahead of time | More documentation and more paths to test |
| **Auto-apply is opt-in, graded and capped** | Submit every match, or never submit unprompted | Some people want the least work possible, and filling in forms is the lowest-value part of a search. A grade bar (B or better), a limit of 5 a day and a referral stop keep it from turning into mass-applying | More cold applications than the pick-first flow. The person must keep their standing form answers up to date |
| **Agents look for people outside LinkedIn first** | Have the agent browse LinkedIn for every job | The posting, the company's site and a web search often name the person, at no risk to the account. Browsing LinkedIn is a separate switch, in the person's own browser, a few pages a day | Sometimes the agent returns search links instead of a name |
| **The person sends every message** | Auto-send outreach | A message under someone's name is theirs to send. Auto-sent outreach is how bots get spotted and accounts get flagged | One manual step per message |
| **Referral first, then apply** | Apply immediately, ask for a referral later | Many referral systems only credit a referral made before the application | Some applications wait a day or two for a reply |
| **CSV tracker by default; Google Sheet optional** | Require Google Sheets | Local files need no account or connector, and a scheduled scan needs no agent | Spreadsheet features like dropdowns only come with the Sheet option |
| **Public job feeds only** | Scrape LinkedIn and Indeed directly | Public feeds are stable, allowed and fast. Scraping breaks often and risks blocks. Workday sites are read through the same JSON their careers pages load, with no login or browser | LinkedIn and Indeed are an opt-in extra through a third-party library |
| **Scripts find jobs; agents read single pages** | Let an AI agent browse careers pages each day | Agent page reads cost AI usage on every page, can't run on a schedule, often come back empty on careers sites, and some tools summarize the page, which can drop or change pay and dates | Agents still read one posting when the scan missed it, and check a priority company's careers page on request ([prompts/fetch-pages.md](prompts/fetch-pages.md)) |
| **A written agent contract** (AGENTS.md) | Tie the workflow to one AI tool | Claude, Muse or any agent that can run a command can join | Rules live in prose, so each agent has to follow them |
| **No RAG or vector database** | Index the person's documents for retrieval | A profile is a few pages and fits in one prompt. Retrieval would add setup and maintenance for no accuracy gain | Worth revisiting once the profile grows past what fits in a prompt |

### What I learned from real data

I tested the scan against live feeds and real resumes, and changed the design based on what came back.

- **One employer crowded out the rest.** In an early scan, a single large company took 19 of the 25 slots. Now each scan caps any one company at 5, and the cap is a setting.
- **Benefits text skewed ranking.** "Health insurance" made every job look like a healthcare role. Benefits, pay-disclosure and legal lines are now left out before scoring.
- **Old postings at target companies matter.** A role open for months, at a company where the person has a referral, is still worth seeing. Those roles skip the age filter and show their open date.
- **Parser problems are invisible to the applicant.** The resume check caught fused letters in a real resume that would have made an applicant tracking system read "staffing" as "sta?ing". It now runs on 17 real resumes with no false alarms.
- **Hacker News posts are free text.** Company, title and location are best-effort there, so those jobs are labeled "check" rather than trusted.

### How I'd measure success

| Type | Metric | Why it matters |
|---|---|---|
| **North star** | Interviews per hour spent on the search | Captures both outcome and effort |
| **Inputs** | Share of applications with a referral or a message to a named person | The behavior that most improves response rates |
| | Share of tailored resumes that pass the parser check on the first try | Quality of what goes out |
| | Minutes from scan to first application each day | Friction in the daily loop |
| **Outcome by channel** | Interview rate for Referral vs Hiring manager message vs Cold application | Tells the person where to put next week's effort (`jobhunt stats`) |
| **Guardrails** | Claims on a resume that can't be traced to the profile: **0** | Trust |
| | Messages sent without the person's approval: **0** | Trust |
| | AI usage on a day with no applications (Lean mode): **0** | Cost |

The `stats` command won't rank channels until there are about 20 applications in each. With fewer than that, the differences are noise.

### Risks and mitigations

| Risk | Mitigation |
|---|---|
| The AI overstates experience | Profile-only rule; every number must have a source; the person reviews every resume before it goes out |
| A job board changes its feed | Each source is isolated, so one failure doesn't stop the scan; 114 automated tests run on every change |
| Two agents overwrite each other | Insert-only writes, claiming a job in Notes, and a scan that remembers what it has already shown |
| Personal data leaks | Everything personal lives in `private/`, which git never uploads; the scan sends only ordinary requests for public listings |
| Too complex for non-technical users | A click-by-click setup guide, a guided setup command, and a no-AI mode that works on its own |

### What's next

- **A dry-run setting for auto-apply**, which fills each form and saves a screenshot without submitting, for a first week of checking what would go out.
- **An MCP server**, so any AI tool can use the scan, tracker and checks directly.
- **Presets for other roles** (engineering, design, data, nursing), so setup is one choice instead of a config file.
- **A claim check** that traces every resume bullet back to a line in the person's profile.

**Deliberately not planned:** applying with no grade bar or daily limit, auto-sending messages, and scraping sites that don't offer public feeds.
