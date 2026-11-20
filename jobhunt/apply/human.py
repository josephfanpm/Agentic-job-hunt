"""Hand the browser to the user for the steps only a person should do.

Captchas, sign-ins and identity checks exist to confirm a person is present. This module
never solves or works around them. The rest of the form is filled first; then the user is
told the window needs them, and the run waits until the page moves on.
"""
from __future__ import annotations

import subprocess
import sys
import time

CAPTCHA_FRAMES = ("recaptcha/api2/bframe", "recaptcha/enterprise/bframe", "hcaptcha.com/captcha", "newassets.hcaptcha.com",
                  "challenges.cloudflare.com", "arkoselabs", "funcaptcha", "captcha-delivery")
CAPTCHA_TEXT = ("verify you are human", "verify you're human", "are you a robot",
                "complete the security check", "press and hold")


def captcha_showing(page) -> bool:
    """True when a challenge a person must answer is on screen (not an invisible badge)."""
    try:
        for fr in page.frames:
            if any(k in (fr.url or "") for k in CAPTCHA_FRAMES):
                el = fr.frame_element()
                box = el.bounding_box()
                if box and box["width"] > 120 and box["height"] > 120 and el.is_visible():
                    return True
        body = (page.inner_text("body", timeout=3000) or "").lower()
        return any(t in body for t in CAPTCHA_TEXT)
    except Exception:
        return False


SIGNIN_TEXT = ("verify your email", "enter your password", "log in or create account", "sign in to continue",
               "sign in to your account", "create an account to apply", "enter verification code")


def signin_showing(page, url_pattern: str = "") -> bool:
    """True on a sign-in, password or account-verification page. Those belong to the user:
    the tool never types into them or presses their buttons."""
    import re
    try:
        if url_pattern and re.search(url_pattern, page.url):
            return True
        if page.locator('input[type="password"]:visible').count():
            return True
        body = (page.inner_text("body", timeout=3000) or "").lower()
        return len(body) < 2500 and any(t in body for t in SIGNIN_TEXT)
    except Exception:
        return False


def _q(s: str) -> str:
    return s.replace("'", "").replace('"', "")[:180]


def notify(title: str, message: str) -> None:
    """Best-effort desktop notice plus a terminal line. Never raises."""
    print(f"\a>>> {title}: {message}", flush=True)
    try:
        if sys.platform == "win32":
            ps = ("Add-Type -AssemblyName System.Windows.Forms;"
                  "$n = New-Object System.Windows.Forms.NotifyIcon;"
                  "$n.Icon = [System.Drawing.SystemIcons]::Information; $n.Visible = $true;"
                  f"$n.ShowBalloonTip(15000, '{_q(title)}', '{_q(message)}', 'Info'); Start-Sleep 16; $n.Dispose()")
            subprocess.Popen(["powershell", "-NoProfile", "-WindowStyle", "Hidden", "-Command", ps],
                             stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        elif sys.platform == "darwin":
            subprocess.Popen(["osascript", "-e",
                              f'display notification "{_q(message)}" with title "{_q(title)}" sound name "Glass"'])
        else:
            subprocess.Popen(["notify-send", title, message])
    except Exception:
        pass


def wait_for_user(page, why: str, done, timeout: int = 900, title: str = "Job application needs you") -> bool:
    """Tell the user what the window needs, then wait until `done(page)` is true.
    Returns False if the time runs out. The form stays filled either way."""
    try:
        page.bring_to_front()
    except Exception:
        pass
    notify(title, why)
    end = time.time() + timeout
    nudged = time.time()
    while time.time() < end:
        try:
            if done(page):
                return True
        except Exception:
            pass
        if time.time() - nudged > 240:
            notify(title, why)
            nudged = time.time()
        page.wait_for_timeout(2000)
    return False
