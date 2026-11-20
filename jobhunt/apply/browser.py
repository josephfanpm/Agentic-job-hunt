"""One real browser window with a profile kept between runs, so a site the user signed
in to once (a careers account, for example) stays signed in."""
from __future__ import annotations

from .. import config


def profile_dir():
    d = config.home() / "browser-profile"
    d.mkdir(parents=True, exist_ok=True)
    return d


def open_browser(p, cfg: dict):
    """Returns a persistent browser context. Uses the installed Chrome when there is one."""
    channel = cfg["auto_apply"].get("browser") or "chrome"
    kw = dict(user_data_dir=str(profile_dir()), headless=False, viewport={"width": 1280, "height": 900})
    try:
        return p.chromium.launch_persistent_context(channel=channel, **kw)
    except Exception:
        return p.chromium.launch_persistent_context(**kw)


def need_playwright() -> str:
    try:
        import playwright  # noqa: F401
        return ""
    except ImportError:
        return "Filling forms needs Playwright:  pip install playwright   (it drives the browser you already have)"
