"""
Persistent browser session.

Why persistent: LinkedIn/Naukri/Indeed require login. Instead of automating
login (which is exactly the pattern that gets flagged), we open a real
Chromium profile, let YOU log in manually the first time, and reuse that
same profile (with cookies) on every future run. To the site, this just
looks like you opening your browser again.
"""

import random
import time
from pathlib import Path
from playwright.sync_api import sync_playwright

PROFILE_DIR = Path(__file__).parent.parent / "data" / "browser_profile"
PROFILE_DIR.mkdir(parents=True, exist_ok=True)


def get_browser_context(headless: bool = False):
    """
    Launches a persistent Chromium context. First run: you'll need to
    manually log into LinkedIn/Naukri/Indeed in the window that opens.
    After that, cookies are reused automatically.
    """
    playwright = sync_playwright().start()
    context = playwright.chromium.launch_persistent_context(
        user_data_dir=str(PROFILE_DIR),
        headless=headless,
        viewport=None,  # let --start-maximized control size
        args=["--disable-blink-features=AutomationControlled", "--start-maximized"],
    )
    return playwright, context


def human_delay(delay_range=(3, 12)):
    """Sleep a random amount to avoid obvious bot-timing patterns."""
    time.sleep(random.uniform(*delay_range))


def human_type(locator, text: str):
    """Type character-by-character with small random delays, like a person."""
    for ch in text:
        locator.type(ch, delay=random.randint(40, 140))
