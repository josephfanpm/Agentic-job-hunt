"""Send scan results to a Google Sheet through its Apps Script receiver.

The receiver (sheet/apps-script.gs) runs inside the user's own sheet, so the
scan can write there from any computer without Google Cloud credentials,
connectors or AI calls.
"""
from __future__ import annotations

import datetime as dt
import json
import urllib.error
import urllib.request

from jobhunt import net, sheet
from jobhunt.models import Job

_LABELS = {"greenhouse": "Greenhouse", "lever": "Lever", "ashby": "Ashby", "workable": "Workable",
           "remoteok": "Remote OK", "remotive": "Remotive", "weworkremotely": "We Work Remotely",
           "himalayas": "Himalayas", "hackernews": "Hacker News", "amazon": "amazon.jobs",
           "linkedin": "LinkedIn", "indeed": "Indeed", "zip_recruiter": "ZipRecruiter",
           "glassdoor": "Glassdoor"}


def source_label(source: str) -> str:
    return _LABELS.get(source.split(":")[-1], source)


def rows(jobs: list[Job], cfg: dict, today: dt.date | None = None) -> list[dict]:
    """One {header: value} dict per job. The receiver matches headers by name."""
    out = []
    for rank, job in enumerate(jobs, start=1):
        v = sheet.job_values(job, rank, cfg, today)
        v["Link"] = {"url": job.url, "label": source_label(job.source)}
        v["LinkedIn search"] = [{"label": label, "query": q, "url": url}
                                for label, q, url in v["LinkedIn search"]]
        out.append(v)
    return out


def send(url: str, token: str, payload_rows: list[dict], timeout: int = 90,
         expire_after_days: int = 0, keep_companies: list[str] | None = None,
         email: bool = False, email_top: int = 10) -> dict:
    """POST rows to the receiver. Returns its reply, e.g. {"ok": true, "added": 3}.

    The receiver also tidies the sheet: applied jobs move to Applied, and jobs
    older than expire_after_days move to Archive (keep_companies are exempt).
    With email=True it emails you the top new jobs, each with a Pick link.
    """
    return _post(url, token, {"rows": payload_rows, "expire_after_days": expire_after_days,
                              "keep_companies": keep_companies or [], "email": bool(email),
                              "email_top": int(email_top)}, timeout)


def picks(url: str, token: str, timeout: int = 60) -> list[dict]:
    """Rows of Daily jobs ticked Pick and not yet Applied, as {header: value}."""
    return _post(url, token, {"action": "picks"}, timeout).get("picks", [])


def _post(url: str, token: str, body: dict, timeout: int) -> dict:
    if not url or not token:
        raise ValueError("sheet_webhook and sheet_token must both be set in config")
    data = json.dumps({"token": token, **body}, ensure_ascii=False).encode("utf-8")
    req = urllib.request.Request(url, data=data, method="POST", headers={
        "Content-Type": "application/json", "User-Agent": net.USER_AGENT})
    # Apps Script answers a POST with a redirect to the result, which urllib
    # follows as a GET: exactly what's needed.
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            body = resp.read().decode("utf-8", errors="replace")
    except urllib.error.HTTPError as e:
        raise net.FetchError(f"sheet receiver: HTTP {e.code}") from e
    except (urllib.error.URLError, TimeoutError, OSError) as e:
        raise net.FetchError(f"sheet receiver: {getattr(e, 'reason', e)}") from e
    try:
        reply = json.loads(body)
    except ValueError:
        # An HTML page usually means the web app isn't deployed for "Anyone"
        raise net.FetchError("sheet receiver didn't answer with JSON. Check the deployment's "
                             "access is set to 'Anyone' (see sheet/README-apps-script.md)")
    if not reply.get("ok"):
        raise net.FetchError(f"sheet receiver refused: {reply.get('error', reply)}")
    return reply
