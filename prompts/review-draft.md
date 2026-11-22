# Review a tailored resume and cover letter

A second reader catches what the writer can't: a claim that drifted from the profile, a top third that doesn't answer "does this person fit?", a cover letter that could go to any company. Run this after [tailor-resume.md](tailor-resume.md) compiles and the check passes, and before anything is submitted.

**When:** for every tailored resume in Standard and Full modes, including auto-apply. In Lean mode, only when the user asks.

## Who reviews

The reviewer must not be the agent that wrote the draft, or must start fresh:

- **If your tool can start a sub-agent** (Claude Code's Agent tool, Codex sub-tasks and the like), start one with only the files listed below and this prompt. Don't pass it your notes or reasoning: it should judge the page, not your intent.
- **If it can't,** do the review as a separate step: re-read the files below from disk, not from memory, and argue against the draft.
- A second agent working the same tracker can review too. Claim it in Notes first: `Codex 2026-11-22: reviewing`.

## What the reviewer reads

1. The job description from `private/jds/` (only the text above any section the posting check set aside)
2. `private/profile.md`
3. The resume's text: `python -m jobhunt check <resume>.pdf --jd <jd file>` and `python -m jobhunt check <resume>.pdf --bullets`
4. The cover letter, if there is one
5. The company brief in `private/research/<Company>.md`. If there isn't one and a cover letter is going out, write it first with [research.md](research.md)

## What to check

1. **Every claim traces to the profile.** For each bullet and each sentence of the letter, find the line in `private/profile.md` that supports it: the title, the employer, the dates, the number, the tool. List each one you can't find. This is the most important check; nothing else matters if it fails.
2. **The top third answers the question.** Read only the top third of page 1, as a recruiter would in the first few seconds. Does it show a match for the posting's top two or three needs? If not, which bullet lower down should move up?
3. **The posting's top needs are covered.** List the three to five things the job description asks for most. For each, name the bullet that shows it, or say "not shown". "Not shown" is a fix only if the profile has the experience.
4. **The letter is about this company.** Does it name one specific, true, sourced detail about the team or product? Could it go to a competitor by changing the name? If yes, it fails.
5. **Plain language.** Flag internal feature names, unexplained acronyms and anything a recruiter outside the user's company couldn't picture.
6. **The resume rules.** Strong verb openers, a sourced number where one exists, no filler, every listed tool shown in a bullet ([tailor-resume.md](tailor-resume.md#resume-rules)).

## Output

A numbered list of fixes, most important first, at most eight. Each fix has: the line as written, what's wrong, and the change, using only facts from the profile. Then one verdict line:

- **Ready**: no unsupported claims, and nothing on the list would change a recruiter's first read.
- **Fix first**: anything else.

Don't rewrite the whole resume, and don't suggest adding anything the profile doesn't support. "Add a metric here" is only a fix if the profile has the number.

## After the review

The writer applies the fixes that are true, recompiles, and runs `python -m jobhunt check` again. If the verdict was **Fix first** because of an unsupported claim, review once more after fixing. Stop after two rounds: if it still isn't ready, write `waiting: review` in Notes and hand it to the user with the remaining fixes.

Save the review next to the application: `private/applications/<Company>__<Role>/review.md`.
