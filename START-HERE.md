# Start here: setup without coding experience

You don't need to be a programmer to use this. If you can install an app and copy and paste, you can set it up in about 20 minutes. This page walks through every click.

You don't need an AI tool to start. Finding jobs, ranking them, finding people to contact and checking your resume all work without one. Step 6 covers adding AI later.

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

**Option A: the Claude desktop app (does the most for you).** Install the [Claude app](https://claude.com/download) for Mac or Windows and open its **Code** tab. Point it at the project folder, then ask in plain English, for example: *"Read AGENTS.md, then tailor my resume for the Acme job in today's list."* It runs the commands above for you, edits files and can update a Google Sheet.

**Option B: any AI chat (no install).** Use Claude, ChatGPT or another chat site. It can't run commands or open your files, so you do those parts:
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

## Step 8. Run it every morning (optional)

**Windows:**
1. Open **Task Scheduler** and click **Create Basic Task**. Name it "Job scan" and choose **Daily**.
2. For **Program**, type `python`. For **Arguments**, type `-m jobhunt scan`.
3. For **Start in**, paste your project folder's location. Copy it from File Explorer's address bar.

**Mac:** open the AI app or a terminal each morning and run `python3 -m jobhunt scan`.

Or just run the scan yourself each morning; it takes a few seconds.

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
