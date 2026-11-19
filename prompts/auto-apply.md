# Auto-apply (Full mode)

Use this only when `python -m jobhunt mode` shows `mode: full` and `auto-apply: on`. If auto-apply is off, prepare the application and stop; the user submits ([MODES.md](../MODES.md)).

With auto-apply on, the agent submits applications for the best new jobs without asking first. The user's remaining job is to send the message drafted for each one.

## Which jobs qualify

Run this after the scan and [evaluate.md](evaluate.md). A job qualifies when all of these are true:

- Its grade is `auto_apply.min_grade` or better (B by default), and the grade came from the real job description in `private/jds/`.
- It isn't in the Applied tab (match Company + Role), Applied isn't ticked, and no other agent claimed it today.
- Today's count of Applied rows with Channel **Auto-apply** is below `auto_apply.max_per_day` (5 by default).

Work the best grade first, then the newest posting. Jobs over the daily limit wait for tomorrow. Jobs the user ticked Pick are handled by [work-picks.md](work-picks.md) and don't count toward the limit.

## Stop and hand the job back

Prepare everything you can, write `waiting: <reason>` in Notes, and don't submit when:

- **A referral is possible.** `python -m jobhunt network find "Company"` shows a warm contact (they replied, endorsed or recommended the user), or the company is in `priority_companies`.
- **The form asks something the profile doesn't answer.** Use the **Application answers** section of `private/profile.md` word for word. If a sponsorship or work-authorization question isn't covered there, or is worded differently enough that the written answer might not be true for it (for example "now or in the future"), stop. Never guess.
- **The site wants an account, a password, a verification code, a captcha, an assessment or a video.** If the user's browser is already signed in to that site, carry on. Never create an account, type a password or work around a wall (Rule 11 in [AGENTS.md](../AGENTS.md)).
- **The form asks the user to agree to more than "these answers are true":** a background check, an arbitration or non-compete agreement, or a signature.
- **The resume fails `python -m jobhunt check`,** or you couldn't get the real job description.
- **The posting has changed:** it's closed, or its title or location no longer matches the saved description.

## For each job

1. **Claim it** in Notes: `Claude 2026-11-18: auto-apply`.
2. **Tailor** with [tailor-resume.md](tailor-resume.md). The check must pass.
3. **Fill the form** by the rules in [apply.md](apply.md), step 3.
4. **Keep a record before submitting.** Save `private/applications/<Company>__<Role>/answers.md` with every question and the answer you entered. Add a screenshot of the finished form if your tool can take one.
5. **Submit once.** Wait for the confirmation page or message. If you can't tell whether it went through, don't submit again: write `submitted? check email` in Notes.
6. **Log it** in the Applied tab with Channel **Auto-apply**, and tick Applied.
7. **Find the person** with [find-person.md](find-person.md) and put them in the Hiring manager cell.
8. **Draft one message** with [outreach.md](outreach.md) in the Message cell. Never send it.
9. **Set Follow up on** to 7 days out.

Work one application at a time. If a job site slows you down or returns an error page, stop using that site for the day.

## Report back

Start with **Messages to send today**: one line per submitted job with the company, the role, the person's name, title and link, and where the draft is. Then list what's **waiting on the user** and why, and what was **left for tomorrow**.
