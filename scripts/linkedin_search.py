"""Build LinkedIn search cells (three clickable lines each) for the job sheet.

Input: a JSON list of jobs, one per sheet row:
    [{"row": 2, "company": "DoorDash", "team": ["merchant", "marketplace"],
      "big": true, "peer_titles": ["product manager"]}, ...]
  - company: plain name; it is quoted automatically when it has a space.
    Pass a list (["Joist", "EverPro"]) to OR several names together.
  - team: optional keywords (phrases get quoted).
  - big: optional; adds (product OR tech OR technical) to the recruiter search.
  - peer_titles: optional; defaults to ["product manager"].

Usage:
    python scripts/linkedin_search.py jobs.json --sheet-id 1 --col 16 > requests.json
Then send requests.json with the Sheets connector's update_spreadsheet.
--col is the 0-based column index of "LinkedIn search" (16 = column Q in the
default schema).
"""
import argparse
import json
import urllib.parse

RECRUITER = ["recruiter", "talent acquisition", "sourcer"]
MANAGER = ["director of product", "head of product", "group product manager",
           "VP of product", "senior manager, product"]
BASE = "https://www.linkedin.com/search/results/people/?keywords="


def term(t):
    return f'"{t}"' if " " in t else t


def group(items):
    items = [term(t) for t in items]
    return items[0] if len(items) == 1 else "(" + " OR ".join(items) + ")"


def queries(job):
    names = job["company"] if isinstance(job["company"], list) else [job["company"]]
    company = group(names)
    team = group(job["team"]) if job.get("team") else None
    peers = group(job.get("peer_titles") or ["product manager"])
    rec = [group(RECRUITER)]
    if job.get("big"):
        rec.append("(product OR tech OR technical)")
    rec.append(company)
    join = lambda *p: " AND ".join(x for x in p if x)
    return [("Recruiters: ", join(*rec)),
            ("Hiring managers: ", join(group(MANAGER), company, team)),
            ("Peers: ", join(peers, company, team))]


def cell(job):
    text, runs = "", []
    lines = queries(job)
    for i, (label, q) in enumerate(lines):
        runs.append({"startIndex": len(text),
                     "format": {"link": {"uri": BASE + urllib.parse.quote(q, safe="()")}}})
        text += label + q + ("\n" if i < len(lines) - 1 else "")
    return {"userEnteredValue": {"stringValue": text}, "textFormatRuns": runs}


def requests(jobs, sheet_id, col):
    return [{"updateCells": {
        "start": {"sheetId": sheet_id, "rowIndex": j["row"] - 1, "columnIndex": col},
        "rows": [{"values": [cell(j)]}],
        "fields": "userEnteredValue,textFormatRuns"}} for j in jobs]


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("jobs")
    p.add_argument("--sheet-id", type=int, default=1)
    p.add_argument("--col", type=int, default=16)
    a = p.parse_args()
    jobs = json.load(open(a.jobs, encoding="utf-8"))
    print(json.dumps(requests(jobs, a.sheet_id, a.col), separators=(",", ":")))
