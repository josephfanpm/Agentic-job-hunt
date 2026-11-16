"""Run the scan from a scheduler (Windows log-on, cron, launchd) without a window.

- Runs at most once per day, so logging in and out repeatedly doesn't rescan.
- Waits up to 5 minutes for the internet after start-up.
- Writes everything to private/logs/scan.log, keeping the last 2,000 lines.

Usage: pythonw scripts/scheduled_scan.py [--force]
"""
from __future__ import annotations

import contextlib
import datetime as dt
import io
import socket
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from jobhunt import cli, config  # noqa: E402


def online(host: str = "boards-api.greenhouse.io", wait_seconds: int = 300) -> bool:
    deadline = time.time() + wait_seconds
    while True:
        try:
            socket.create_connection((host, 443), timeout=5).close()
            return True
        except OSError:
            if time.time() > deadline:
                return False
            time.sleep(10)


def main() -> int:
    home = config.home()
    logs = home / "logs"
    logs.mkdir(parents=True, exist_ok=True)
    log_file = logs / "scan.log"
    marker = home / "state" / "last_scheduled_scan.txt"
    today = dt.date.today().isoformat()
    force = "--force" in sys.argv

    buf = io.StringIO()
    code = 0
    with contextlib.redirect_stdout(buf), contextlib.redirect_stderr(buf):
        print(f"=== {dt.datetime.now():%Y-%m-%d %H:%M} scheduled scan")
        cfg = config.load()
        if cfg["tracker"] == "sheet" and not (cfg.get("sheet_webhook") and cfg.get("sheet_token")):
            # Without the receiver, results couldn't reach the sheet and would be lost
            print("tracker is a Google Sheet but sheet_webhook isn't set up; skipping. "
                  "See sheet/README-apps-script.md")
            code = 2
        elif not force and marker.exists() and marker.read_text().strip() == today:
            print("already ran today; skipping (use --force to run again)")
        elif not online():
            print("no internet connection after 5 minutes; will try at the next log-on")
            code = 1
        else:
            try:
                code = cli.main(["scan"])
            except Exception as e:  # never die silently in the background
                print(f"scan crashed: {type(e).__name__}: {e}")
                code = 1
            if code == 0:
                marker.parent.mkdir(parents=True, exist_ok=True)
                marker.write_text(today)

    old = log_file.read_text(encoding="utf-8").splitlines() if log_file.exists() else []
    lines = (old + buf.getvalue().splitlines())[-2000:]
    log_file.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return code


if __name__ == "__main__":
    raise SystemExit(main())
