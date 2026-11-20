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
- **The form asks something only the user can answer.** `python -m jobhunt apply` answers from `private/answers.json` and stops, unsent, at a required question with no saved answer. For those, use your judgment (see *Questions with no saved answer* below). Stop only for a work-authorization, sponsorship or citizenship question that the bank doesn't cover, or a question the profile gives you nothing to answer from.
- **The site wants an assessment or a video,** or a sign-in the user hasn't done. Never create an account, type a password, solve a captcha or work around a wall (Rule 11 in [AGENTS.md](../AGENTS.md)). The `apply` command covers the rest: it reads an emailed security code when `email_codes` is set up, and at an "are you human" check or a sign-in page it notifies the user and waits. If the wait runs out, write `waiting: human check` or `waiting: sign in (python -m jobhunt signin <url>)` in Notes and move on.
- **The form asks the user to agree to more than "these answers are true":** a background check, an arbitration or non-compete agreement, or a signature.
- **The resume fails `python -m jobhunt check`,** or you couldn't get the real job description.
- **The posting has changed:** it's closed, or its title or location no longer matches the saved description.

## Questions with no saved answer

When the dry run lists a question the bank doesn't cover, answer it yourself from `private/profile.md` instead of handing the job back:

- **Pick the answer that helps the candidate most among the ones the profile supports.** Read experience generously: related work counts, and so does experience gained in another role or sector. "Do you have experience with A/B testing?" is Yes for someone who ran experiments under another name.
- **Never enter something the profile contradicts.** A count of years, a degree, a licence, a clearance or a past employer is checked against the resume attached to the same form and again in the background check. A false answer there gets the application rejected or the offer withdrawn. If the true answer fails the screen, enter the true answer and say so in the report; the user decides whether to apply anyway.
- **Essays:** write them by the rules in [apply.md](apply.md), step 3.
- **Voluntary questions with no saved answer:** choose the decline option.
- Save every answer you chose in the job's `answers.json`, and list them under **Answers I chose** in the report, so the user can correct one and save it to the bank with `python -m jobhunt answers add`.

## For each job

1. **Claim it** in Notes: `Claude 2026-11-18: auto-apply`.
2. **Tailor** with [tailor-resume.md](tailor-resume.md). The check must pass.
3. **Fill the form** with `python -m jobhunt apply <url> --company "Company" --role "Role" --resume <pdf> --country <US|CA|...> --dry-run`, adding `--cover <pdf>` when you wrote a cover letter. Read its output. If it lists unanswered questions, answer them by *Questions with no saved answer* above, save them in the job's folder as `answers.json` (`{"words from the question": "answer"}`), and run the dry run again. If your agent has no terminal, fill the form by hand by the rules in apply.md.
4. **Keep a record before submitting.** Save `private/applications/<Company>__<Role>/answers.md` with every question and the answer you entered. Add a screenshot of the finished form if your tool can take one.
5. **Submit once:** the same command without `--dry-run`. It prints `SUBMITTED` only after the confirmation page. Wait for the confirmation page or message. If you can't tell whether it went through, don't submit again: write `submitted? check email` in Notes.
6. **Log it** in the Applied tab with Channel **Auto-apply**, and tick Applied.
7. **Find the person** with [find-person.md](find-person.md) and put them in the Hiring manager cell.
8. **Draft one message** with [outreach.md](outreach.md) in the Message cell. Never send it.
9. **Set Follow up on** to 7 days out.

Work one application at a time. If a job site slows you down or returns an error page, stop using that site for the day.

## Report back

Start with **Answers I chose**, if any: the question, the answer and the company. Then **Messages to send today**: one line per submitted job with the company, the role, the person's name, title and link, and where the draft is. Then list what's **waiting on the user** and why, and what was **left for tomorrow**.
