# Check email for replies (needs a Gmail connector)

Run this when the user asks, or once a day in Standard and Full modes. Skip it if Gmail isn't connected.

1. **Search only for job mail.** Look for emails from the last 14 days from the companies in the Applied tab, or from known applicant tracking systems (Greenhouse, Lever, Ashby, Workday, iCIMS, SmartRecruiters). Don't read anything else in the inbox.
2. **Sort each email:**
   - **Interview invite or scheduling request:** set Status to Recruiter screen (first call) or Interviewing (later rounds). Tell the user right away with the company, the role and any date or link.
   - **Rejection:** set Status to Rejected. Clear Follow up on.
   - **Recruiter or hiring manager reply:** leave Status alone, note the reply in Notes and draft an answer. If the person is in the Network tab, the user updates that row's Status (it's theirs).
   - **"We received your application":** no change.
3. **Draft, never send.** Save every reply or follow-up as a Gmail draft, using [outreach.md](outreach.md) or [follow-up.md](follow-up.md). Put the draft's first line in the tracker's Notes column so the user knows it's waiting.
   With the CSV tracker, edit the matching row in `private/tracker/applied.csv`, changing only those cells.
4. **Report** in 3–5 lines: new interviews first, then replies with drafts waiting, then rejections.

Never send, delete, archive or label an email, and never reply to a scheduling link for the user. If an email asks for something not in `private/profile.md`, such as references or availability, ask the user.
