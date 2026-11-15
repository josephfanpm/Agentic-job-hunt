# Review what's working

Run this weekly in Full mode, or monthly on request. The goal is one decision: where to spend next week's effort.

## Numbers

- **CSV tracker:** `python -m jobhunt stats` gives applications, interviews and offers per channel.
- **Google Sheet:** read the Applied tab's Status, Channel, Applied date and Role columns and count the same.

Report:

| Measure | How |
|---|---|
| Applications sent | Rows in Applied, this period and in total |
| Interview rate by channel | Rows that reached "Recruiter screen" or later ÷ applications, per channel |
| Reply rate on messages | Network rows with status Replied or later ÷ rows messaged |
| Time to first response | Days from applied to first status change |
| Where things stall | The stage with the biggest drop: no response, screen, or later rounds |

## Read the numbers honestly

- **Give the counts with every rate.** "1 of 3" is not "33%".
- **Under about 20 applications in a channel, don't rank channels.** Say it's too early, and what count would be enough.
- Jobs applied to in the last two weeks may still get a reply. Leave them out of rates, or say they're included.
- Look for a pattern in the rejections and the screens: level, domain, location, pay. Name it only if at least three cases share it.

## Decide

End with at most three changes for the next period, each tied to a number:

- Stalling before any reply → more referrals and messages, fewer cold applications.
- Getting screens but not second rounds → practice with [mock-interview.md](mock-interview.md), and tighten answers.
- Few matches in the scan → widen titles or sources in the config.
- Replies but no referrals → make the ask more specific: job ID, resume attached.

Save the review to `private/reviews/<date>.md`, so the next one can compare.
