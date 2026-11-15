"""Turn sheet/schema.json into one Google Sheets batchUpdate request list.

Usage:
    python scripts/build_sheet_requests.py [--rows 500] > requests.json

Run it against a brand-new, empty spreadsheet. It adds one tab per schema
entry and then deletes the default "Sheet1" (sheetId 0). The agent passes
the output to the Sheets connector's update_spreadsheet (batchUpdate) call.
Tab sheetIds are fixed as 1, 2, 3... in schema order, so later steps can
address tabs by id.
"""
import argparse
import json
from pathlib import Path

SCHEMA = Path(__file__).resolve().parent.parent / "sheet" / "schema.json"


def rng(sheet_id, r0, r1, c0, c1):
    return {"sheetId": sheet_id, "startRowIndex": r0, "endRowIndex": r1,
            "startColumnIndex": c0, "endColumnIndex": c1}


def build(rows):
    schema = json.loads(SCHEMA.read_text(encoding="utf-8"))
    r, g, b = schema["header_color"]
    reqs = []
    for i, tab in enumerate(schema["tabs"], start=1):
        cols = tab["columns"]
        n = len(cols)
        reqs.append({"addSheet": {"properties": {
            "sheetId": i, "title": tab["name"], "index": i - 1,
            "gridProperties": {"rowCount": rows, "columnCount": n,
                               "frozenRowCount": tab.get("frozen_rows", 1)}}}})
        # Header row
        reqs.append({"updateCells": {
            "start": {"sheetId": i, "rowIndex": 0, "columnIndex": 0},
            "rows": [{"values": [{
                "userEnteredValue": {"stringValue": c["name"]},
                "userEnteredFormat": {
                    "backgroundColorStyle": {"rgbColor": {"red": r, "green": g, "blue": b}},
                    "textFormat": {"bold": True, "foregroundColorStyle": {"rgbColor": {"red": 1, "green": 1, "blue": 1}}},
                    "wrapStrategy": "WRAP", "verticalAlignment": "MIDDLE"}} for c in cols]}],
            "fields": "userEnteredValue,userEnteredFormat"}})
        # Body: wrap + top alignment
        reqs.append({"repeatCell": {
            "range": rng(i, 1, rows, 0, n),
            "cell": {"userEnteredFormat": {"wrapStrategy": "WRAP", "verticalAlignment": "TOP"}},
            "fields": "userEnteredFormat.wrapStrategy,userEnteredFormat.verticalAlignment"}})
        for j, c in enumerate(cols):
            reqs.append({"updateDimensionProperties": {
                "range": {"sheetId": i, "dimension": "COLUMNS", "startIndex": j, "endIndex": j + 1},
                "properties": {"pixelSize": c.get("width", 120)}, "fields": "pixelSize"}})
            body = rng(i, 1, rows, j, j + 1)
            if c.get("type") == "checkbox":
                reqs.append({"setDataValidation": {"range": body, "rule": {"condition": {"type": "BOOLEAN"}}}})
            if c.get("type") == "date":
                reqs.append({"repeatCell": {"range": body,
                    "cell": {"userEnteredFormat": {"numberFormat": {"type": "DATE", "pattern": "yyyy-mm-dd"}}},
                    "fields": "userEnteredFormat.numberFormat"}})
            if c.get("dropdown"):
                reqs.append({"setDataValidation": {"range": body, "rule": {
                    "condition": {"type": "ONE_OF_LIST",
                                  "values": [{"userEnteredValue": v} for v in c["dropdown"]]},
                    "showCustomUi": True, "strict": False}}})
            if c.get("formula"):
                reqs.append({"updateCells": {
                    "start": {"sheetId": i, "rowIndex": 1, "columnIndex": j},
                    "rows": [{"values": [{"userEnteredValue": {"formulaValue": c["formula"].format(row=k)}}]}
                             for k in range(2, rows + 1)],
                    "fields": "userEnteredValue"}})
    reqs.append({"deleteSheet": {"sheetId": 0}})
    return reqs


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--rows", type=int, default=500)
    print(json.dumps(build(p.parse_args().rows), separators=(",", ":")))
