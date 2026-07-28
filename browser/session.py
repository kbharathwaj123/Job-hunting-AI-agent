"""
Persistent browser session with automatic lock cleanup, screenshot capture,
and background headless support for locked laptop execution.
"""

import os
import re
import random
import time
import subprocess
from pathlib import Path
from playwright.sync_api import sync_playwright

PROFILE_DIR = Path(__file__).parent.parent / "data" / "browser_profile"
SCREENSHOTS_DIR = Path(__file__).parent.parent / "data" / "screenshots"
PROFILE_DIR.mkdir(parents=True, exist_ok=True)
SCREENSHOTS_DIR.mkdir(parents=True, exist_ok=True)


def cleanup_stale_browser_locks():
    """Removes leftover Chrome profile locks if a previous run was interrupted."""
    lock_files = ["SingletonLock", "SingletonCookie", "SingletonSocket", "lockfile"]
    for lock in lock_files:
        lock_path = PROFILE_DIR / lock
        if lock_path.exists():
            try:
                os.remove(lock_path)
                print(f"  [SESSION FIX 🧹] Cleared stale browser lock: {lock}")
            except Exception:
                pass


def kill_orphaned_chrome_processes():
    """Kills leftover orphaned Playwright chromium instances on Windows if profile is locked."""
    try:
        if os.name == "nt":
            subprocess.run(
                ["taskkill", "/F", "/IM", "chrome.exe", "/FI", "MODULES eq chrome.dll"],
                capture_output=True,
                check=False
            )
            time.sleep(1)
    except Exception:
        pass


def capture_confirmation_screenshot(page, company_name: str) -> str:
    """Captures a screenshot of the application confirmation/staged page for proof."""
    try:
        clean_company = re.sub(r'[^a-zA-Z0-9]', '_', company_name)[:20]
        timestamp = int(time.time())
        filename = f"proof_{clean_company}_{timestamp}.png"
        filepath = SCREENSHOTS_DIR / filename
        
        page.screenshot(path=str(filepath), full_page=False)
        print(f"  [PROOF CAPTURED 📸] Saved screenshot: {filename}")
        return str(filepath).replace("\\", "/")
    except Exception as e:
        print(f"  [SCREENSHOT WARNING] Could not capture screenshot: {e}")
        return ""


def get_browser_context(headless: bool = False):
    """
    Launches a persistent Chromium context. Automatically handles background execution
    when laptop is locked by configuring headless viewport & backgrounding flags.
    """
    cleanup_stale_browser_locks()
    playwright = sync_playwright().start()

    browser_args = [
        "--disable-blink-features=AutomationControlled",
        "--disable-background-timer-throttling",
        "--disable-backgrounding-occluded-windows",
        "--disable-renderer-backgrounding",
        "--no-sandbox",
        "--disable-dev-shm-usage"
    ]
    
    viewport_setting = None
    if headless:
        viewport_setting = {"width": 1920, "height": 1080}
    else:
        browser_args.append("--start-maximized")

    for attempt in range(2):
        try:
            context = playwright.chromium.launch_persistent_context(
                user_data_dir=str(PROFILE_DIR),
                headless=headless,
                viewport=viewport_setting,
                args=browser_args,
            )
            return playwright, context
        except Exception as e:
            err_str = str(e).lower()
            if "processsingleton" in err_str or "lock file" in err_str or "32" in err_str:
                print(f"\n[SESSION WARNING] Chromium profile was locked. Cleaning up (attempt {attempt + 1})...")
                kill_orphaned_chrome_processes()
                cleanup_stale_browser_locks()
                time.sleep(2)
            else:
                raise e

    # Final attempt
    context = playwright.chromium.launch_persistent_context(
        user_data_dir=str(PROFILE_DIR),
        headless=headless,
        viewport=viewport_setting,
        args=browser_args,
    )
    return playwright, context


def human_delay(delay_range=(2, 6)):
    """Sleep a random amount to avoid obvious bot-timing patterns."""
    time.sleep(random.uniform(*delay_range))


def human_type(locator, text: str):
    """Type character-by-character with small random delays, like a person."""
    for ch in text:
        locator.type(ch, delay=random.randint(30, 100))
