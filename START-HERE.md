# Start here: setup without coding experience

You don't need to be a programmer to use this. There are two ways to set it up:

- **Let an AI app do it (about 10 minutes).** Install one app, paste one message, and answer its questions. See below.
- **Do it yourself (about 20 minutes).** Follow Steps 1 to 5. Every click is written out.

After setup, the daily job scan runs without AI. You only need AI for writing tailored resumes, cover letters and messages.

---

## The fastest way: let an AI app set it up

You need an AI app that can work with files on your computer. A regular chat website can't do this. Any of these works, and none needs a code editor or other extra software:

| App | Cost | Sign in with |
|---|---|---|
| [Google Antigravity](https://antigravity.google) | Free, with a weekly limit | A Google account |
| [ChatGPT desktop app](https://openai.com/chatgpt/download/), **Codex** mode | Free, with a small limit. More with Plus (about $20 a month) | A ChatGPT account |
| [Claude desktop app](https://claude.com/download), **Code** tab | Claude Pro (about $20 a month) or higher | A Claude account |
| [Grok Build](https://x.ai/cli) | Included with SuperGrok or X Premium+. It runs in a terminal window, so it's a little less friendly | An X or Grok account |
| VS Code with an open model | Free or pennies a job. Takes a few extra steps ([see below](#using-a-free-or-open-model-in-vs-code)) | A model provider account |

Free plans are plenty for setup. If you later want AI to tailor a resume for every job, a free plan may run out within the week. A paid plan, or Option B in Step 6, covers that.

Free limits change often, so check the app's pricing page if one stops working.

**1. Make a folder.** Create an empty folder called `job-hunt` in your Documents folder. Put your resume PDF in it.

**2. Open the folder in the app.** Install the app, sign in, and choose **Open folder** (or the folder picker in the Codex mode or Code tab). Pick the `job-hunt` folder.

**3. Paste this message and press Enter:**

```
Set up the job search tool from https://github.com/josephfanpm/agentic-job-hunt in this folder.

I'm not technical. Please:
- Explain each step in one plain sentence, with no technical words.
- Run every command yourself. Never ask me to type one.
- Ask me one question at a time, with an example answer.
- Only show me errors if something went wrong, and say in plain words what you'll do about it.

Steps:
1. Make sure Python 3 is installed. If it isn't, install it, or tell me exactly what to click.
2. Download the project into this folder: use git if it's installed, otherwise download and unzip the ZIP.
3. Open prompts/setup.md in the project and follow it from start to finish. It covers my job search questions, connecting Google Sheets and Gmail if I want them, an interview about my jobs, projects and results, and my first job search.
```

**4. Allow its steps and answer its questions.** The app asks before it runs a command or changes a file. That's normal: click **Allow** or **Run**. It also asks about:

- **What you're looking for:** job titles, pay, countries, and companies you like.
- **Google Sheet or files on your computer:** if you pick the Sheet, it asks you to connect your Google account in the app's settings (usually **Settings → Connectors**), then builds the sheet for you.
- **Gmail (optional):** if you connect it, the AI saves messages to recruiters as drafts in your Gmail and spots replies and interview invites. It never sends anything.
- **Your experience (20–40 minutes):** each job you've had, what the company does, your projects and their results. This lets it write a different resume for each job instead of reusing one. You can stop and finish later.

If you're unsure about a question, say so; it's fine to skip.

If the app gets stuck, finish with the matching step below. For example, if Python won't install, do Step 1 yourself and then tell the app to carry on.

---

## Step 1. Install Python (5 minutes, once)

Python is the free program that runs this tool.

**Windows**
1. Go to [python.org/downloads](https://www.python.org/downloads/) and click the yellow **Download Python** button.
2. Open the file you downloaded.
3. **Important:** on the first screen, tick **"Add python.exe to PATH"** at the bottom. Then click **Install Now**.

**Mac**
1. Go to [python.org/downloads](https://www.python.org/downloads/) and click **Download Python**.
2. Open the file you downloaded and click through the installer.
3. On a Mac, type `python3` wherever this guide says `python`.

## Step 2. Download this project (1 minute)

1. At the top of [the project page](https://github.com/josephfanpm/agentic-job-hunt), click the green **Code** button, then **Download ZIP**.
2. Find the ZIP in your Downloads folder and unzip it. On Windows, right-click it and choose **Extract All**; on a Mac, double-click it.
3. Move the unzipped folder somewhere easy to find, such as your Documents folder.

## Step 3. Open a terminal in that folder (1 minute)

A terminal is a window where you type commands. You'll only use a handful, and you can copy them from this page.

**Windows:** open the project folder in File Explorer. Click the address bar at the top, type `cmd`, and press **Enter**. A black window opens, already in the right folder.

**Mac:** open the **Terminal** app (search for it with Cmd+Space). Type `cd ` (with a space after it), drag the project folder into the Terminal window, and press **Enter**.

To paste a command, right-click in the window (Windows) or press Cmd+V (Mac), then press **Enter**.

## Step 4. Install the tool's parts (1 minute, once)

Paste this and press Enter:

```
python -m pip install -r requirements.txt
```

Text scrolls by for a few seconds. It's finished when you can type again.

**If you see "python is not recognized"** (Windows), Python wasn't added to PATH. Run the Python installer again, choose **Modify**, and tick **"Add Python to environment variables"**. Then close the terminal and open a new one.

## Step 5. Set up your search (5 minutes)

Put your resume (a PDF) in the project folder. Then paste this, using your resume's file name:

```
python -m jobhunt init --resume my-resume.pdf
```

It asks a few questions. Press Enter to skip any you're unsure about; you can change them later.

| Question | Example answer |
|---|---|
| Job titles to search for | `product manager, senior product manager` |
| Words that rule a title out | `intern, director` |
| Topics you want more of | `healthcare, marketplace` |
| Countries you can work in | `US, CA` (two-letter codes) |
| Include remote roles? | `y` |
| Lowest yearly pay you'd accept | `90000` |
| Companies where someone would refer you | `Acme` |
| Other companies to watch | `Globex, Initech` |
| Google Sheet or local files? | `csv` (simplest: files you open in Excel) |
| How much should AI do? | `lean` |

Then find today's jobs:

```
python -m jobhunt scan
```

You'll see a ranked list. Each job has a score, the pay when the posting states it, a short reason it fits, and a link. The same list is saved to `private/tracker/daily_jobs.csv`, which you can open in Excel, Numbers or Google Sheets. Each row also has three LinkedIn links to find a recruiter, a hiring manager and someone already doing the job.

Your personal files stay in the `private` folder on your computer and are never uploaded.

**Next, build your experience bank** (20–40 minutes, once). Your resume only has room for some of what you've done. Ask an AI from Step 6 to interview you about each job, project and result, so every tailored resume can pick what fits that job. With an app that works with your files, say *"Run prompts/profile-interview.md"*. With a chat site, paste [prompts/profile-interview.md](prompts/profile-interview.md) and your resume, then copy the result into the Experience bank section of `private/profile.md`.

### Commands you'll use

| To | Paste |
|---|---|
| Find new jobs | `python -m jobhunt scan` |
| Check your resume before sending it | `python -m jobhunt check my-resume.pdf` |
| See who you already know at a company | `python -m jobhunt network find "Company"` (after you add your LinkedIn data; see below) |
| Find people to contact at a company | `python -m jobhunt people "Company" "Job title"` |
| Record that you applied | `python -m jobhunt applied "Company"` |
| See who to follow up with today | `python -m jobhunt due` |
| Add a company to watch | `python -m jobhunt boards add "Company"` |

### Your daily routine (10 minutes)

1. **Pick jobs.** Open your Google Sheet (on your computer or in the Google Sheets phone app) and tick **Pick** next to 2–5 jobs you like. With the morning email turned on, click **Pick this job** in the email instead.
2. **Hand them over.** Open your AI app on your computer, open your `job-hunt` folder, and type **work my picks**.
3. **Send and apply.** Come back later: each picked job has a tailored resume and a draft message. Read them, send the messages yourself, and answer anything the app asks.

This needs an AI app that works with files on your computer (see above). A chat website such as chatgpt.com can't read your sheet or files, so it can't do step 2.

### Add your LinkedIn data (optional)

This takes 5 minutes of clicking, then up to a day of waiting. A referral from someone you know beats any cold application, so the tool should know who you know.

1. On a computer (the phone app can't do this), open LinkedIn and click **Me** → **Settings & Privacy** → **Data privacy** → **Get a copy of your data**.
2. Choose the larger archive (the first option, with everything), then **Request archive**.
3. LinkedIn emails you twice: a first file within minutes, and the full archive within 24 hours. Wait for the full one. The download link works for 72 hours.
4. Unzip it, then paste: `python -m jobhunt network build "<the unzipped folder>"`

Now `python -m jobhunt network find "Company"` lists everyone you know there, warmest first, plus invitations they haven't accepted. Run it before you apply anywhere.

## Step 6. Add an AI assistant (optional)

AI writes the tailored resumes, cover letters, messages and interview practice. Pick whichever fits you:

**Option A: an AI app that works with your files (does the most for you).** Use any app from [the table at the top](#the-fastest-way-let-an-ai-app-set-it-up): Google Antigravity (free), ChatGPT's Codex mode (free or paid), Claude's Code tab (paid), Grok Build (paid), or VS Code with an open model (below). Open the project folder in it and paste the first message from [prompts/kickoff.md](prompts/kickoff.md). The AI then helps with the whole search: the daily list, tailored resumes, messages, follow-ups, interview practice and offers. After that, ask in plain English, for example: *"Tailor my resume for the Acme job in today's list."*

Already use VS Code? The Claude Code, Codex and GitHub Copilot extensions work there too. Copilot has a free plan with a small monthly limit. You don't need VS Code if you use one of the apps above.

**Option B: any AI chat (no install, works on free plans).** Use Grok, ChatGPT, Claude, Gemini or another chat site. It can't run commands or open your files, so you do those parts:
1. Start a chat, or a project if your site has them, attach `AGENTS.md` and `private/profile.md`, and paste the second message from [prompts/kickoff.md](prompts/kickoff.md).
2. For each task, paste the instruction file you need from the `prompts` folder, such as `prompts/tailor-resume.md`, and the job description the scan saved in `private/jds/`.
3. Copy the result back out.

**Option C: no AI.** The scan, people searches, resume check and tracker all work without it. Write your own resumes and messages, with the files in `prompts/` as checklists.

### Using a free or open model in VS Code

This is the cheapest option, and it takes about 15 minutes to set up. Choose it if you're comfortable copying a key into a settings screen.

1. **Install [VS Code](https://code.visualstudio.com)** (free) and open it.
2. **Add Cline.** Click the **Extensions** icon on the left (four small squares), search for **Cline**, and click **Install**. A Cline icon appears on the left.
3. **Get a model key.** Pick one:
   - **[OpenRouter](https://openrouter.ai) (free models available):** sign up, go to **Keys**, click **Create key**, and copy it. Models with "free" in the name cost nothing but have a daily limit and can be slow at busy times.
   - **[DeepSeek](https://platform.deepseek.com) (pennies a job):** sign up, add a few dollars of credit, go to **API keys**, create one and copy it. Tailoring a resume costs a few cents.
4. **Connect Cline.** Click the Cline icon, choose your provider (OpenRouter or DeepSeek), paste the key, and pick a model. If you're unsure which, choose the largest DeepSeek or Qwen model on offer.
5. **Open your folder.** Click **File → Open Folder** and pick the `job-hunt` folder.
6. **Paste the setup message** from [the top of this page](#the-fastest-way-let-an-ai-app-set-it-up) into Cline. After setup, use the kickoff message in [prompts/kickoff.md](prompts/kickoff.md).

Keep in mind:
- Your resume and profile go to the model's company. DeepSeek's own service stores data in China.
- Open and free models make more mistakes on long tasks than the paid apps. Read every tailored resume closely, and run `python -m jobhunt check` before you send one.
- You can also run a model on your own computer with [Ollama](https://ollama.com). It's free and private, but it needs a powerful computer (about 24 GB of memory), and the small models a normal laptop can run often fail at this work.

If you'd rather not set up a key, Google Antigravity is free with just a Google account.

## Step 7. Turn your resume into a PDF (optional)

Tailored resumes are written in LaTeX, a format that produces clean, consistent PDFs. You don't need to install anything to use it:

1. Sign up free at [overleaf.com](https://www.overleaf.com) and click **New Project → Upload Project**.
2. Upload your `.tex` resume file, such as `private/resume.tex`.
3. Click **Menu** (top left), set **Compiler** to **XeLaTeX**, then click **Recompile**.
4. Click **Download PDF**, then run `python -m jobhunt check` on the downloaded file.

## Step 8. Run it automatically (optional)

Paste this once:

```
python -m jobhunt schedule on
```

From then on, the scan runs by itself a minute after you log in to your computer, at most once a day, in the background. It works on Windows, Mac and Linux. To also run it at a set time each day, add `--at 08:00`.

| To | Paste |
|---|---|
| Check it's on | `python -m jobhunt schedule status` |
| Turn it off | `python -m jobhunt schedule off` |
| See what it did | Open `private/logs/scan.log` |

Old jobs tidy themselves: anything you haven't applied to after 14 days moves to an Archive file, and jobs you've applied to move to the Applied list.

---

## Something went wrong?

| You see | Do this |
|---|---|
| `python is not recognized` or `command not found` | Windows: see the note in Step 4. Mac: use `python3` instead of `python`. |
| `No module named jobhunt` | The terminal isn't in the project folder. Redo Step 3. |
| `No job titles set` | Run `python -m jobhunt init` again, and answer the job titles question. |
| The scan finds nothing | Widen your titles, or add companies with `boards add`. The scan also prints why it skipped jobs, such as "too old" or "outside your countries". |
| Not sure what's set up | Run `python -m jobhunt doctor`. It lists anything missing. |

Next: [GUIDE.md](GUIDE.md) covers the daily routine, and [MODES.md](MODES.md) explains how much the AI does in each mode.
