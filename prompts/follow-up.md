# Follow-ups

Most replies come after a nudge. One nudge, then stop.

## What's due

- **CSV tracker:** `python -m jobhunt due` lists applications and contacts whose follow-up date has arrived.
- **Google Sheet:** read only the "Follow up on" and "Status" columns of the Applied and Network tabs, and list rows that are due and still open.

## Write the nudge

Reply in the same thread as the first message. Keep it under 60 words:

1. One line that adds something new: a result, a relevant launch of theirs, or that you've now applied.
2. The same small ask as before.

Don't write "just following up", "bumping this" or "circling back". Don't apologize for writing.

| Situation | Add |
|---|---|
| Messaged a hiring manager, no reply | A result of yours that fits something the team shipped or announced since |
| Asked for a referral, no reply | Make it easier: the job ID, your resume attached, and "no worries if not" |
| Applied, no response after 7 days | Message the recruiter or a peer on the team; use `python -m jobhunt people` to find one |
| Interviewed, no word after the date they gave | Ask the recruiter for a timeline, and restate your interest in one line |

## After sending

The user sends it. Then move the follow-up date out 7 days once. If that passes with no reply, set the status to "No response" (applications) or "No reply" (contacts) and move on.
