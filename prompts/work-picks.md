# Work my picks

Use this when the user says "work my picks" (or "do my picks", "apply to what I picked"). Picks are the jobs they ticked **Pick** in Daily jobs: in the sheet, on their phone, or from the morning email.

## 1. Get the list

Run `python -m jobhunt picks`. It lists ticked jobs that aren't applied yet, with pay, location, who they know there, the link and the saved job description. It works for both trackers, and for the Google Sheet once the receiver is set up.

If it says the receiver isn't set up, read the **Daily jobs** tab with your Sheets connector instead: rows where Pick is ticked and Applied isn't.

If the user has no tracker access at all (a chat website), ask them to paste the jobs they want.

Skip a job when:
- its Resume cell is already filled (it's done; say so in the summary)
- its Notes show another agent claimed it today

## 2. Work each job, one at a time

1. **Claim it.** Write your name and today's date in Notes, for example `Claude 2026-11-18: working pick`.
2. **Check who they know.** Run `python -m jobhunt network find "Company"`. If someone there is warm (replied, endorsed or recommended them), stop on this job and ask whether to request a referral before applying.
3. **Tailor and apply** with [apply.md](apply.md): resume, check, cover letter if the form takes one, form, log.
4. **Draft one message** with [outreach.md](outreach.md) and put it in the Message cell.
5. **Leave Pick ticked.** Ticking Applied (you, or the user) moves the row to the Applied tab.

## 3. Report back

One short list, one line per job: done, waiting on the user (and what for: a referral, a sponsorship question, a login or captcha), or skipped (and why). End with the messages the user should send today.
