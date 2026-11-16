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

Free plans are plenty for setup. If you later want AI to tailor a resume for every job, a free plan may run out within the week. A paid plan, or Option B in Step 6, covers that.

Free limits change often, so check the app's pricing page if one stops working.

**1. Make a folder.** Create an empty folder called `job-hunt` in your Documents folder. Put your resume PDF in it.

**2. Open the folder in the app.** Install the app, sign in, and choose **Open folder** (or the folder picker in the Codex mode or Code tab). Pick the `job-hunt` folder.

**3. Paste this message and press Enter:**

```
Set up the job search tool from https://github.com/josephfanpm/agentic-job-hunt in this folder. I'm not a programmer, so tell me what each step does in one plain sentence and do the work yourself.

1. Check that Python 3 is installed. If it isn't, install it, or tell me exactly what to click.
2. Download the project into this folder. Use git if it's installed; otherwise download the ZIP and unzip it.
3. Install its requirements with: python -m pip install -r requirements.txt
4. Read START-HERE.md and AGENTS.md.
5. Ask me the setup questions from Step 5 of START-HERE.md one at a time, in plain language. Find my resume PDF in this folder. Then run "python -m jobhunt init" with my answers as flags plus --yes, so I don't have to use the interactive setup.
6. Run "python -m jobhunt doctor" and fix anything it reports. Then run "python -m jobhunt scan" and show me my top 10 jobs.
7. Ask me if I want the scan to run by itself every day. If I say yes, run "python -m jobhunt schedule on".
```

**4. Allow its steps.** The app asks before it runs a command or changes a file. That's normal: click **Allow** or **Run**. If it asks you something you're unsure about, it's fine to say so.

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

### Commands you'll use

| To | Paste |
|---|---|
| Find new jobs | `python -m jobhunt scan` |
| Check your resume before sending it | `python -m jobhunt check my-resume.pdf` |
| Find people to contact at a company | `python -m jobhunt people "Company" "Job title"` |
| Record that you applied | `python -m jobhunt applied "Company"` |
| See who to follow up with today | `python -m jobhunt due` |
| Add a company to watch | `python -m jobhunt boards add "Company"` |

## Step 6. Add an AI assistant (optional)

AI writes the tailored resumes, cover letters, messages and interview practice. Pick whichever fits you:

**Option A: an AI app that works with your files (does the most for you).** Use any app from [the table at the top](#the-fastest-way-let-an-ai-app-set-it-up): Google Antigravity (free), ChatGPT's Codex mode (free or paid) or Claude's Code tab (paid). Open the project folder in it, then ask in plain English, for example: *"Read AGENTS.md, then tailor my resume for the Acme job in today's list."* It runs the commands above for you, edits files and can update a Google Sheet.

Already use VS Code? The Claude Code, Codex and GitHub Copilot extensions work there too. Copilot has a free plan with a small monthly limit. You don't need VS Code if you use one of the apps above.

**Cheapest pay-as-you-go option (for people comfortable with settings).** Install [VS Code](https://code.visualstudio.com) and its free [Cline](https://cline.bot) extension. Then connect Cline to a low-cost open model:

- **[DeepSeek](https://platform.deepseek.com):** add a few dollars of credit and paste your API key into Cline's settings. Tailoring a resume costs a few cents.
- **[OpenRouter](https://openrouter.ai):** one account for many models. Some are free with a daily limit; free ones can be slow at busy times.

Keep in mind:
- Your resume and profile go to the model's company. DeepSeek's own service stores data in China.
- Smaller models make more mistakes on multi-step work. Read tailored resumes closely, and run `python -m jobhunt check` before you send one.
- Running a model on your own computer (for example with Ollama) is free and private. But it needs a powerful computer, and the small models a normal laptop can run often fail at this kind of work.

If you'd rather not set up an API key, Google Antigravity is free with just a Google account.

**Option B: any AI chat (no install, works on free plans).** Use Claude, ChatGPT, Gemini or another chat site. It can't run commands or open your files, so you do those parts:
1. Open the instruction file you need from the `prompts` folder, such as `prompts/tailor-resume.md`, and copy its text into the chat.
2. Attach `private/profile.md` and the job description, which the scan saved in `private/jds/`.
3. Copy the result back out.

**Option C: no AI.** The scan, people searches, resume check and tracker all work without it. Write your own resumes and messages, with the files in `prompts/` as checklists.

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
