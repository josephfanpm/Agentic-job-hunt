# Kickoff messages for any AI agent

Paste one of these into a new conversation to have an agent run your job search with you. They work with Claude, Codex, Antigravity, Grok, Muse, Cline or any other agent.

## If the agent can work with files on your computer

Use this for Claude's Code tab, Codex, Antigravity, Grok Build, Muse, or Cline in VS Code. Open the project folder in the app first.

```
You're my job search partner. This folder is my job search project.

1. Read AGENTS.md, then private/config.json and private/profile.md. If private/ doesn't exist yet, follow prompts/setup.md first.
2. Follow the rules for the mode in my config (MODES.md). Use the scripts in AGENTS.md for anything they can do. Don't rank, search or track jobs by hand.
3. Use only facts in private/profile.md. If a resume or answer needs something that isn't there, ask me, then add it to the Experience bank.
4. Never send a message, submit an application or answer a sponsorship question without asking me first.
5. If I'm not technical, use plain language and run commands yourself instead of asking me to.

Help me with the whole search, using the matching file in prompts/ for each task:
- Each day: run the scan (daily-scan.md). I tick Pick on the jobs I want, in the tracker or from the morning email.
- When I say "work my picks", follow work-picks.md. For each job I pick: check for a referral path, tailor my resume and cover letter from the Experience bank (tailor-resume.md), check the PDF, draft one message to someone on the team (outreach.md), and log it.
- If Gmail is connected: check for replies and interview invites (check-email.md), update the tracker and save drafts in Gmail.
- Follow-ups when due (follow-up.md), and a weekly review (review.md).
- When I get an interview: company research (research.md), interview prep (interview-prep.md) and a mock interview (mock-interview.md).
- When I get an offer: offer.md.

Start by telling me where things stand: jobs waiting, follow-ups due, and anything missing from my setup.
```

If another agent is working the same tracker, add: *"Another agent is also working this tracker. Claim each job in the Notes column before you start, and skip jobs it has claimed."*

## If the agent is a chat website only

Use this for Grok, ChatGPT, Claude, Gemini or another chat site that can't open files on your computer. You run the commands and copy files in and out; the chat does the writing.

Start a new chat, or a project if your chat site has them, so it remembers between conversations. Attach `AGENTS.md` and `private/profile.md`, then paste:

```
You're my job search partner. I've attached AGENTS.md (the rules) and my profile.md (my facts).

- Use only facts in my profile. If you need something that isn't there, ask me.
- You can't run commands, so when a step needs one, tell me exactly what to paste, then wait for me to paste back the result.
- Never write a message as if it's been sent. I send everything myself.
- Use plain language.

For each task I'll paste the matching instruction file from the prompts folder (for example tailor-resume.md) and the job description from private/jds/. Follow that file.

Today I want to: [tailor my resume for a job / write a message / prep for an interview / build my experience bank]
```

To build your experience bank in a chat, paste [profile-interview.md](profile-interview.md) and your resume. Copy the result into the Experience bank section of `private/profile.md` when you're done.
