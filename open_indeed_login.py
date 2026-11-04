"""
Helper script to open Indeed in the agent's persistent browser.
Allows you to log into your Indeed account (or complete 2FA / Google SSO / CAPTCHA) once.
The session cookies and local storage are saved permanently in data/browser_profile.
"""

import sys
import time
from browser.session import get_browser_context

def main():
    print("===========================================================")
    print("            INDEED PERSISTENT LOGIN LAUNCHER               ")
    print("===========================================================")
    print("Opening visible browser with your agent's persistent profile...")
    
    playwright, context = get_browser_context(headless=False)
    page = context.new_page()
    
    # Navigate to Indeed sign in page
    login_url = "https://secure.indeed.com/auth"
    print(f"Navigating to: {login_url}")
    page.goto(login_url)
    
    print("\n>> Browser window is open on your screen!")
    print(">> Please complete your login (Google SSO, Email/Password, OTP, or CAPTCHA).")
    print(">> When you're finished logging in, you can simply close the browser window.")
    print(">> All cookies and session state are automatically saved for the Job Agent.\n")
    
    try:
        while True:
            time.sleep(2)
            if page.is_closed() or len(context.pages) == 0:
                break
    except KeyboardInterrupt:
        pass
    finally:
        try:
            context.close()
        except Exception:
            pass
        try:
            playwright.stop()
        except Exception:
            pass
        print("[SUCCESS] Browser session saved to data/browser_profile!")

if __name__ == "__main__":
    main()
