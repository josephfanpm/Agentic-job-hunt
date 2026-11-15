"""Build Google Sheets batchUpdate requests, so no agent hand-types them.

Two jobs: create the whole sheet from sheet/schema.json, and insert the
day's scan results under the header of "Daily jobs". An agent passes the
output to its Sheets connector in one call.
"""
from __future__ import annotations

import datetime as dt
import json
from pathlib import Path

from jobhunt import people
from jobhunt.config import ROOT
from jobhunt.models import Job

SCHEMA_PATH = ROOT / "sheet" / "schema.json"


def load_schema(path: Path | None = None) -> dict:
    return json.loads((path or SCHEMA_PATH).read_text(encoding="utf-8"))


def columns(tab_name: str, schema: dict | None = None) -> list[dict]:
    schema = schema or load_schema()
    return next(t for t in schema["tabs"] if t["name"] == tab_name)["columns"]


def _rng(sheet_id, r0, r1, c0, c1):
    return {"sheetId": sheet_id, "startRowIndex": r0, "endRowIndex": r1,
            "startColumnIndex": c0, "endColumnIndex": c1}


def create_requests(rows: int = 500, schema: dict | None = None) -> list[dict]:
    """Requests that turn a brand-new spreadsheet into the tracker.

    Tabs get sheetIds 1, 2, 3... in schema order, and the default "Sheet1"
    (sheetId 0) is deleted, so run this on an empty file only.
    """
    schema = schema or load_schema()
    r, g, b = schema["header_color"]
    reqs: list[dict] = []
    for i, tab in enumerate(schema["tabs"], start=1):
        cols = tab["columns"]
        n = len(cols)
        reqs.append({"addSheet": {"properties": {
            "sheetId": i, "title": tab["name"], "index": i - 1,
            "gridProperties": {"rowCount": rows, "columnCount": n,
                               "frozenRowCount": tab.get("frozen_rows", 1)}}}})
        reqs.append({"updateCells": {
            "start": {"sheetId": i, "rowIndex": 0, "columnIndex": 0},
            "rows": [{"values": [{
                "userEnteredValue": {"stringValue": c["name"]},
                "userEnteredFormat": {
                    "backgroundColorStyle": {"rgbColor": {"red": r, "green": g, "blue": b}},
                    "textFormat": {"bold": True, "foregroundColorStyle": {
                        "rgbColor": {"red": 1, "green": 1, "blue": 1}}},
                    "wrapStrategy": "WRAP", "verticalAlignment": "MIDDLE"}} for c in cols]}],
            "fields": "userEnteredValue,userEnteredFormat"}})
        reqs.append({"repeatCell": {
            "range": _rng(i, 1, rows, 0, n),
            "cell": {"userEnteredFormat": {"wrapStrategy": "WRAP", "verticalAlignment": "TOP"}},
            "fields": "userEnteredFormat.wrapStrategy,userEnteredFormat.verticalAlignment"}})
        for j, c in enumerate(cols):
            reqs.append({"updateDimensionProperties": {
                "range": {"sheetId": i, "dimension": "COLUMNS", "startIndex": j, "endIndex": j + 1},
                "properties": {"pixelSize": c.get("width", 120)}, "fields": "pixelSize"}})
            body = _rng(i, 1, rows, j, j + 1)
            if c.get("type") == "checkbox":
                reqs.append({"setDataValidation": {"range": body, "rule": {"condition": {"type": "BOOLEAN"}}}})
            if c.get("type") == "date":
                reqs.append({"repeatCell": {"range": body, "cell": {"userEnteredFormat": {
                    "numberFormat": {"type": "DATE", "pattern": "yyyy-mm-dd"}}},
                    "fields": "userEnteredFormat.numberFormat"}})
            if c.get("dropdown"):
                reqs.append({"setDataValidation": {"range": body, "rule": {
                    "condition": {"type": "ONE_OF_LIST",
                                  "values": [{"userEnteredValue": v} for v in c["dropdown"]]},
                    "showCustomUi": True, "strict": False}}})
            if c.get("formula"):
                reqs.append({"updateCells": {
                    "start": {"sheetId": i, "rowIndex": 1, "columnIndex": j},
                    "rows": [{"values": [{"userEnteredValue": {
                        "formulaValue": c["formula"].format(row=k)}}]} for k in range(2, rows + 1)],
                    "fields": "userEnteredValue"}})
    reqs.append({"deleteSheet": {"sheetId": 0}})
    return reqs


# ---- daily rows --------------------------------------------------------------
def job_values(job: Job, rank: int, cfg: dict, today: dt.date | None = None) -> dict:
    """One job as {column name: plain value}, shared by the sheet and CSV trackers."""
    today = today or dt.date.today()
    remote = "Remote" if job.remote else ""
    note = f"via {job.source}" + (f" · ID {job.job_id}" if job.job_id and len(job.job_id) < 40 else "")
    return {
        "Applied": False, "Scanned": today.isoformat(), "Rank": rank, "Company": job.company,
        "Role": job.title, "Pay": job.pay, "Location": job.location, "Work type": remote,
        "Posted": job.posted, "Why it fits": job.why, "Link": job.url, "Notes": note,
        "LinkedIn search": people.for_job(job.company, job.title, cfg),
    }


_BODY_FORMAT = {"wrapStrategy": "WRAP", "verticalAlignment": "TOP"}


def _cell(col: dict, value) -> dict:
    name = col["name"]
    if name == "LinkedIn search":
        c = people.cell(value)
    elif col.get("type") == "checkbox":
        c = {"userEnteredValue": {"boolValue": bool(value)},
             "dataValidation": {"condition": {"type": "BOOLEAN"}}}
    elif name == "Link" and value:
        label = "Open"
        safe = str(value).replace('"', "%22")
        c = {"userEnteredValue": {"formulaValue": f'=HYPERLINK("{safe}","{label}")'}}
    elif isinstance(value, (int, float)) and not isinstance(value, bool):
        c = {"userEnteredValue": {"numberValue": value}}
    else:
        c = {"userEnteredValue": {"stringValue": "" if value is None else str(value)}}
    c["userEnteredFormat"] = _BODY_FORMAT
    return c


def row_requests(jobs: list[Job], cfg: dict, today: dt.date | None = None,
                 schema: dict | None = None) -> list[dict]:
    """Insert the jobs as new rows directly under the Daily jobs header.

    Existing rows shift down untouched, which is what keeps two agents from
    overwriting each other.
    """
    if not jobs:
        return []
    cols = columns("Daily jobs", schema)
    sheet_id = cfg["sheet_tab_ids"]["Daily jobs"]
    rows = []
    for rank, job in enumerate(jobs, start=1):
        values = job_values(job, rank, cfg, today)
        rows.append({"values": [_cell(c, values.get(c["name"], "")) for c in cols]})
    return [
        {"insertDimension": {"range": {"sheetId": sheet_id, "dimension": "ROWS",
                                       "startIndex": 1, "endIndex": 1 + len(jobs)},
                             "inheritFromBefore": False}},
        {"updateCells": {"start": {"sheetId": sheet_id, "rowIndex": 1, "columnIndex": 0},
                         "rows": rows,
                         "fields": "userEnteredValue,userEnteredFormat,textFormatRuns,dataValidation"}},
    ]
