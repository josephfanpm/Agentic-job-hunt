"""One real Chrome window that stays open between runs, with its own kept profile.

The window is started once and left running; each run attaches to it, works in a new tab
and leaves the window open. A site the user signed in to (a careers account, for example)
therefore stays signed in, including sites that sign you out when the browser closes.
"""
from __future__ import annotations

import shutil
import subprocess
import sys
import time
import urllib.request
from pathlib import Path

from .. import config

CHROME_PATHS = (
    r"C:\Program Files\Google\Chrome\Application\chrome.exe",
    r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
    "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
)


def profile_dir() -> Path:
    d = config.home() / "browser-profile"
    d.mkdir(parents=True, exist_ok=True)
    return d


def chrome_path() -> str:
    for c in CHROME_PATHS:
        if Path(c).exists():
            return c
    local = Path.home() / "AppData/Local/Google/Chrome/Application/chrome.exe"
    if local.exists():
        return str(local)
    return shutil.which("google-chrome") or shutil.which("chrome") or shutil.which("chromium") or ""


def _port(cfg: dict) -> int:
    return int(cfg["auto_apply"].get("browser_port") or 9333)


def _running(port: int) -> bool:
    try:
        with urllib.request.urlopen(f"http://127.0.0.1:{port}/json/version", timeout=2):
            return True
    except Exception:
        return False


def start_window(cfg: dict, url: str = "about:blank") -> bool:
    """Start the kept Chrome window if it isn't running. It outlives this command."""
    port = _port(cfg)
    if _running(port):
        return True
    exe = chrome_path()
    if not exe:
        return False
    args = [exe, f"--remote-debugging-port={port}", f"--user-data-dir={profile_dir()}",
            "--no-first-run", "--no-default-browser-check", url]
    kw = {"stdout": subprocess.DEVNULL, "stderr": subprocess.DEVNULL, "stdin": subprocess.DEVNULL}
    if sys.platform == "win32":
        kw["creationflags"] = subprocess.DETACHED_PROCESS | subprocess.CREATE_NEW_PROCESS_GROUP
    else:
        kw["start_new_session"] = True
    subprocess.Popen(args, **kw)
    for _ in range(30):
        if _running(port):
            return True
        time.sleep(0.5)
    return False


class Session:
    """A tab in the kept window (attached), or a browser this run owns (fallback)."""

    def __init__(self, context, attached: bool, browser=None):
        self.context, self.attached, self.browser = context, attached, browser
        self.page = context.new_page() if attached or not context.pages else context.pages[0]

    def close(self) -> None:
        try:
            if not self.attached:
                self.context.close()
            elif len(self.context.pages) > 1:      # never close the last tab: that would close the window
                self.page.close()
        except Exception:
            pass


def open_browser(p, cfg: dict) -> Session:
    """Attach to the kept Chrome window, starting it if needed. Without Chrome installed,
    fall back to a browser that closes with the run (the profile is still kept)."""
    if start_window(cfg):
        browser = p.chromium.connect_over_cdp(f"http://127.0.0.1:{_port(cfg)}")
        return Session(browser.contexts[0], True, browser)
    kw = dict(user_data_dir=str(profile_dir()), headless=False, viewport={"width": 1280, "height": 900})
    return Session(p.chromium.launch_persistent_context(**kw), False)


def need_playwright() -> str:
    try:
        import playwright  # noqa: F401
        return ""
    except ImportError:
        return "Filling forms needs Playwright:  pip install playwright   (it drives the Chrome you already have)"
