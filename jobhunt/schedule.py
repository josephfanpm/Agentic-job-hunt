"""Run the scan automatically on the user's own computer: `python -m jobhunt schedule on`.

Uses the operating system's own scheduler, so nothing needs to stay open:
  - Windows: Task Scheduler (at log-on, plus a daily time if asked)
  - macOS:   a launchd agent in ~/Library/LaunchAgents
  - Linux:   the user's crontab (@reboot, plus a daily time if asked)

Every trigger runs scripts/scheduled_scan.py, which scans at most once a day,
waits for the internet, and logs to private/logs/scan.log. Running the scan
locally avoids two problems with cloud agents: their network often blocks
job sites, and a scheduled agent shares the user's AI usage limit.
"""
from __future__ import annotations

import os
import platform
import shutil
import subprocess
import sys
from pathlib import Path
from xml.sax.saxutils import escape

from jobhunt.config import ROOT

NAME = "agentic-job-hunt scan"
LABEL = "com.agentic-job-hunt.scan"
RUNNER = ROOT / "scripts" / "scheduled_scan.py"
CRON_TAG = "# agentic-job-hunt"


def python_exe(windowless: bool = True) -> str:
    """The interpreter running this, as pythonw on Windows so no window flashes."""
    exe = Path(sys.executable)
    if windowless and os.name == "nt":
        w = exe.with_name("pythonw.exe")
        if w.exists():
            return str(w)
    return str(exe)


def _hhmm(at: str | None) -> tuple[int, int] | None:
    if not at:
        return None
    h, _, m = at.partition(":")
    hour, minute = int(h), int(m or 0)
    if not (0 <= hour < 24 and 0 <= minute < 60):
        raise ValueError("time must look like 08:00")
    return hour, minute


# ---- Windows -----------------------------------------------------------------
def windows_script(logon: bool, at: str | None) -> str:
    """PowerShell that (re)creates the task for the current user. No admin needed."""
    lines = [f"$a = New-ScheduledTaskAction -Execute '{python_exe()}' -Argument '\"{RUNNER}\"' "
             f"-WorkingDirectory '{ROOT}'"]
    names = []
    if logon:
        lines.append("$logon = New-ScheduledTaskTrigger -AtLogOn -User \"$env:USERDOMAIN\\$env:USERNAME\"")
        lines.append("$logon.Delay = 'PT1M'")   # give the network a minute after start-up
        names.append("$logon")
    when = _hhmm(at)
    if when:
        lines.append(f"$daily = New-ScheduledTaskTrigger -Daily -At '{when[0]:02d}:{when[1]:02d}'")
        names.append("$daily")
    lines.append("$s = New-ScheduledTaskSettingsSet -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries "
                 "-StartWhenAvailable -ExecutionTimeLimit (New-TimeSpan -Minutes 30) -MultipleInstances IgnoreNew")
    lines.append(f"Register-ScheduledTask -TaskName '{NAME}' -Action $a -Trigger @({', '.join(names)}) "
                 "-Settings $s -Description 'Scans job boards once a day; log in private\\logs\\scan.log' "
                 "-Force | Out-Null")
    return "; ".join(lines)


def _powershell(cmd: str) -> subprocess.CompletedProcess:
    return subprocess.run(["powershell", "-NoProfile", "-NonInteractive", "-Command", cmd],
                          capture_output=True, text=True)


# ---- macOS -------------------------------------------------------------------
def plist_path() -> Path:
    return Path.home() / "Library" / "LaunchAgents" / f"{LABEL}.plist"


def mac_plist(logon: bool, at: str | None) -> str:
    when = _hhmm(at)
    cal = ""
    if when:
        cal = (f"  <key>StartCalendarInterval</key>\n  <dict><key>Hour</key><integer>{when[0]}</integer>"
               f"<key>Minute</key><integer>{when[1]}</integer></dict>\n")
    return f"""<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
  <key>Label</key><string>{LABEL}</string>
  <key>ProgramArguments</key>
  <array><string>{escape(python_exe(False))}</string><string>{escape(str(RUNNER))}</string></array>
  <key>WorkingDirectory</key><string>{escape(str(ROOT))}</string>
  <key>RunAtLoad</key><{'true' if logon else 'false'}/>
{cal}</dict>
</plist>
"""


# ---- Linux -------------------------------------------------------------------
def cron_lines(logon: bool, at: str | None) -> list[str]:
    cmd = f'cd "{ROOT}" && "{python_exe(False)}" "{RUNNER}"'
    out = []
    if logon:
        out.append(f"@reboot sleep 60 && {cmd} {CRON_TAG}")
    when = _hhmm(at)
    if when:
        out.append(f"{when[1]} {when[0]} * * * {cmd} {CRON_TAG}")
    return out


def _crontab_read() -> list[str]:
    r = subprocess.run(["crontab", "-l"], capture_output=True, text=True)
    return r.stdout.splitlines() if r.returncode == 0 else []


def _crontab_write(lines: list[str]) -> None:
    subprocess.run(["crontab", "-"], input="\n".join(lines) + "\n", text=True, check=True)


# ---- public ------------------------------------------------------------------
def install(logon: bool = True, at: str | None = None) -> str:
    if not logon and not at:
        raise ValueError("choose --logon, --at HH:MM, or both")
    system = platform.system()
    if system == "Windows":
        r = _powershell(windows_script(logon, at))
        if r.returncode:
            raise RuntimeError(r.stderr.strip() or r.stdout.strip())
        return f"Task Scheduler: '{NAME}'"
    if system == "Darwin":
        p = plist_path()
        p.parent.mkdir(parents=True, exist_ok=True)
        subprocess.run(["launchctl", "unload", str(p)], capture_output=True)
        p.write_text(mac_plist(logon, at), encoding="utf-8")
        subprocess.run(["launchctl", "load", str(p)], check=True, capture_output=True)
        return f"launchd agent: {p}"
    if shutil.which("crontab"):
        keep = [ln for ln in _crontab_read() if CRON_TAG not in ln]
        _crontab_write(keep + cron_lines(logon, at))
        return "crontab entries tagged '# agentic-job-hunt'"
    raise RuntimeError("no supported scheduler found (Task Scheduler, launchd or cron)")


def remove() -> str:
    system = platform.system()
    if system == "Windows":
        r = _powershell(f"Unregister-ScheduledTask -TaskName '{NAME}' -Confirm:$false")
        return "removed" if r.returncode == 0 else "no scheduled scan was set up"
    if system == "Darwin":
        p = plist_path()
        if not p.exists():
            return "no scheduled scan was set up"
        subprocess.run(["launchctl", "unload", str(p)], capture_output=True)
        p.unlink()
        return "removed"
    lines = _crontab_read()
    if not any(CRON_TAG in ln for ln in lines):
        return "no scheduled scan was set up"
    _crontab_write([ln for ln in lines if CRON_TAG not in ln])
    return "removed"


def status() -> str:
    system = platform.system()
    if system == "Windows":
        r = _powershell(f"(Get-ScheduledTask -TaskName '{NAME}' -ErrorAction Stop).State")
        return f"on ({r.stdout.strip()})" if r.returncode == 0 else "off"
    if system == "Darwin":
        return "on" if plist_path().exists() else "off"
    return "on" if any(CRON_TAG in ln for ln in _crontab_read()) else "off"
