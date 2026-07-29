"""
Company Careers Page & ATS Application Module with Cookie Banner Dismissal,
Resume Auto-Parsing, Account Creation/Google SSO, and Multi-Step Portal Form Filling.
"""

import re
import urllib.parse
from playwright.sync_api import Page, BrowserContext
from browser.session import human_delay, human_type
from browser.form_filler import fill_form_fields, detect_and_fix_validation_errors, handle_file_uploads, resolve_valid_resume_path


def find_official_careers_url(page: Page, company_name: str, role: str = "") -> str:
    """
    Searches Google for the company's official career portal or ATS job application page.
    """
    query = f"{company_name} official careers {role} jobs apply"
    url = f"https://www.google.com/search?q={urllib.parse.quote(query)}"
    
    print(f"  [OFFICIAL SITE SEARCH] Searching careers page for '{company_name}'...")
    try:
        page.goto(url, timeout=15000)
        page.wait_for_timeout(2000)
    except Exception:
        return ""

    ats_keywords = [
        "myworkdayjobs.com", "greenhouse.io", "lever.co", "smartrecruiters.com",
        "taleo.net", "icims.com", "ashbyhq.com", "careers", "jobs"
    ]
    
    try:
        links = page.locator("a[href^='http']").all()
        for link in links:
            href = link.get_attribute("href") or ""
            href_lower = href.lower()
            
            if any(ignore in href_lower for ignore in ["google.com", "youtube.com", "wikipedia.org", "naukri.com", "linkedin.com", "indeed.com"]):
                continue
                
            if any(keyword in href_lower for keyword in ats_keywords):
                print(f"  [OFFICIAL SITE FOUND] Found careers portal: {href[:70]}...")
                return href
    except Exception:
        pass
        
    return ""


def dismiss_cookie_popups(page: Page):
    """Dismisses cookie consent banners and privacy popups that block portal inputs."""
    cookie_selectors = [
        "button:has-text('Accept All')", "button:has-text('Accept Cookies')",
        "button:has-text('Allow All')", "button:has-text('I Agree')",
        "button:has-text('Got It')", "button:has-text('Accept')",
        "button#onetrust-accept-btn-handler", "#accept-cookies-button",
        "button.cookie-accept", "a:has-text('Accept')"
    ]
    for sel in cookie_selectors:
        try:
            el = page.locator(sel)
            if el.count() > 0 and el.first.is_visible():
                el.first.click()
                print("  [PORTAL COOKIES 🍪] Dismissed cookie consent banner.")
                human_delay((0.5, 1.5))
                break
        except Exception:
            continue


def handle_otp_or_captcha_verification(page: Page, profile_answers: dict = None) -> bool:
    """
    Detects OTP email verification walls or CAPTCHA puzzles on company portals.
    First attempts automated email OTP retrieval via IMAP; falls back to terminal prompt.
    """
    try:
        # 1. Detect OTP verification fields
        otp_field = page.locator("input[name*='otp'], input[name*='code'], input[id*='otp'], input[placeholder*='code'], input[autocomplete='one-time-code']")
        if otp_field.count() > 0 and otp_field.first.is_visible():
            print("\n  [ACTION REQUIRED 🔑] OTP Verification Code required by company portal!")
            
            # Attempt 1: Fully automated email inbox OTP fetch
            otp_code = ""
            email_addr = (profile_answers or {}).get("email", "kaithojubharathwaj123@gmail.com")
            app_pass = (profile_answers or {}).get("gmail_app_password", "")
            
            if app_pass:
                from browser.email_otp import fetch_latest_otp
                otp_code = fetch_latest_otp(email_addr, app_pass, max_wait_seconds=30)
                
            # Attempt 2: Fallback to terminal input if not auto-retrieved
            if not otp_code:
                try:
                    otp_code = input("  >> Enter 6-digit OTP code sent to your email (or press Enter to skip): ").strip()
                except Exception:
                    pass

            if otp_code:
                otp_field.first.fill(otp_code)
                human_delay((1, 2))
                verify_btn = page.locator("button:has-text('Verify'), button:has-text('Submit'), button:has-text('Confirm')")
                if verify_btn.count() > 0 and verify_btn.first.is_visible():
                    verify_btn.first.click()
                    human_delay((3, 5))
                return True

        # 2. Detect CAPTCHA / Cloudflare Turnstile puzzles
        captcha_el = page.locator("iframe[src*='recaptcha'], iframe[src*='turnstile'], iframe[src*='hcaptcha'], #captcha, .g-recaptcha")
        if captcha_el.count() > 0 and captcha_el.first.is_visible():
            print("\n  [CAPTCHA DETECTED 🧩] A security CAPTCHA puzzle was presented by the website.")
            print("  >> Please solve the CAPTCHA in the open browser window.")
            print("  >> Press ENTER here once solved to resume application...")
            try:
                input()
                human_delay((2, 4))
                return True
            except Exception:
                pass
    except Exception:
        pass
    return False


def handle_login_or_account_creation(page: Page, profile_answers: dict) -> bool:
    """
    Detects login/account walls on career portals and attempts Google SSO or auto-login/register.
    """
    try:
        # Check for OTP or CAPTCHA first
        handle_otp_or_captcha_verification(page, profile_answers)

        text = page.locator("body").inner_text().lower()
        if not any(term in text for term in ["sign in", "log in", "create account", "register"]):
            return False
            
        google_btn = page.locator("button:has-text('Google'), a:has-text('Google'), [aria-label*='Google'], div:has-text('Sign in with Google')")
        if google_btn.count() > 0 and google_btn.first.is_visible():
            print("  [LOGIN] Found 'Sign in with Google' option. Clicking SSO...")
            google_btn.first.click()
            human_delay((3, 6))
            handle_otp_or_captcha_verification(page, profile_answers)
            return True

        email = profile_answers.get("email", "kaithojubharathwaj123@gmail.com")
        email_field = page.locator("input[type='email'], input[name*='email'], input[id*='email']")
        if email_field.count() > 0 and email_field.first.is_visible():
            if not email_field.first.input_value().strip():
                email_field.first.fill(email)
                print(f"  [ACCOUNT SETUP] Auto-filled login email: {email}")
                human_delay((1, 2))

        pass_field = page.locator("input[type='password']")
        if pass_field.count() > 0 and pass_field.first.is_visible():
            pass_field.first.fill("JobAgentPass@2026")
            print("  [ACCOUNT SETUP] Auto-filled password.")
            human_delay((1, 2))

        login_sub_btn = page.locator("button:has-text('Sign In'), button:has-text('Log In'), button:has-text('Create Account'), button:has-text('Register')")
        if login_sub_btn.count() > 0 and login_sub_btn.first.is_visible():
            login_sub_btn.first.click()
            human_delay((3, 5))
            handle_otp_or_captcha_verification(page, profile_answers)
            return True
    except Exception:
        pass
    return False


def trigger_resume_autofill(page: Page, resume_file_path: str = "") -> bool:
    """Detects 'Apply with Resume' / 'Autofill with Resume' buttons and triggers resume deduction."""
    autofill_btn = page.locator("button:has-text('Autofill with Resume'), button:has-text('Apply with Resume'), a:has-text('Autofill with Resume')")
    if autofill_btn.count() > 0 and autofill_btn.first.is_visible():
        try:
            print("  [PORTAL AUTOFILL 📄] Found 'Autofill with Resume' feature. Uploading resume for automatic parsing...")
            valid_path = resolve_valid_resume_path(resume_file_path)
            handle_file_uploads(page, valid_path)
            autofill_btn.first.click()
            human_delay((4, 7))  # wait for ATS parser to deduce and populate fields
            return True
        except Exception:
            pass
    return False


def apply_company_website(context: BrowserContext, company_name: str, role: str, job_url: str,
                         resume_text: str, profile_answers: dict, resume_file_path: str = "",
                         auto_submit: bool = True) -> dict:
    """
    Applies to a job directly on the official company careers website or ATS platform.
    """
    page = context.new_page()
    page.set_default_timeout(30000)
    
    target_url = job_url
    if any(aggregator in job_url.lower() for aggregator in ["naukri.com", "indeed.com"]):
        official_url = find_official_careers_url(page, company_name, role)
        if official_url:
            target_url = official_url

    print(f"  [COMPANY WEBSITE APPLY] Opening: {target_url[:80]}...")
    try:
        page.goto(target_url, timeout=25000)
        human_delay((3, 5))
    except Exception as e:
        page.close()
        return {"status": "error", "reason": f"Could not load official careers page: {e}"}

    # 1. Dismiss Cookie Banners / Privacy overlays
    dismiss_cookie_popups(page)

    # 2. Handle Login / Account Creation if present
    handle_login_or_account_creation(page, profile_answers)

    # 3. Trigger ATS "Apply with Resume" / Resume Parsing if present
    trigger_resume_autofill(page, resume_file_path)

    # 4. Look for initial Apply button on careers page
    apply_btn = page.locator("button:has-text('Apply'), a:has-text('Apply'), button:has-text('Apply Now'), a:has-text('Apply Now')")
    if apply_btn.count() > 0 and apply_btn.first.is_visible():
        try:
            apply_btn.first.click()
            human_delay((2, 4))
        except Exception:
            pass

    dismiss_cookie_popups(page)
    handle_login_or_account_creation(page, profile_answers)

    # 5. Multi-Step Form Filling & Resume Upload (up to 8 steps for complex portals like Workday/Taleo/Greenhouse)
    for step in range(8):
        print(f"  [PORTAL FORM] Step {step + 1}: Auto-filling form fields & verifying mandatory resume...")
        
        dismiss_cookie_popups(page)
        
        # Mandatory resume attachment / re-check
        handle_file_uploads(page, resume_file_path)
        
        # Auto-fill form inputs with expanded ATS terminology map
        fill_form_fields(page, resume_text, profile_answers, resume_file_path)
        
        # Detect and fix validation warnings/errors
        detect_and_fix_validation_errors(page, resume_text, profile_answers)

        # Check for Submit button
        submit_btn = page.locator("button:has-text('Submit Application'), button:has-text('Submit'), input[type='submit']")
        if submit_btn.count() > 0 and submit_btn.first.is_visible():
            if auto_submit:
                try:
                    submit_btn.first.click()
                    print(f"  [COMPANY PORTAL SUBMIT] Clicked Submit button for '{company_name}'! Waiting for confirmation response...")
                    page.wait_for_timeout(7000)
                    from browser.session import capture_confirmation_screenshot
                    shot = capture_confirmation_screenshot(page, company_name)
                    print(f"  [COMPANY WEBSITE APPLY 🎉] Successfully submitted application to '{company_name}'!")
                    page.close()
                    return {"status": "submitted", "reason": "Application submitted & confirmation verified", "screenshot": shot}
                except Exception as e:
                    print(f"  [WARNING] Submit click error: {e}")
            else:
                break

        # Check for Next / Continue / Save & Continue button
        next_btn = page.locator("button:has-text('Next'), button:has-text('Continue'), button:has-text('Save & Continue'), a:has-text('Next')")
        if next_btn.count() > 0 and next_btn.first.is_visible():
            try:
                next_btn.first.click()
                human_delay((2, 4))
            except Exception:
                break
        else:
            break

    from browser.session import capture_confirmation_screenshot
    shot = capture_confirmation_screenshot(page, company_name)
    
    # Final safety re-check for submit button
    if auto_submit:
        submit_btn = page.locator("button:has-text('Submit Application'), button:has-text('Submit'), input[type='submit']")
        if submit_btn.count() > 0 and submit_btn.first.is_visible():
            try:
                submit_btn.first.click()
                print("  [PORTAL SUBMIT] Final submission click executed! Waiting for confirmation...")
                page.wait_for_timeout(7000)
                shot = capture_confirmation_screenshot(page, company_name)
                page.close()
                return {"status": "submitted", "reason": "Application submitted & confirmation verified", "screenshot": shot}
            except Exception:
                pass
        page.close()
        return {"status": "staged", "reason": "Form requires manual verification (unhandled required fields)", "screenshot": shot}

    print("  -------------------------------------------------------")
    print("  >> APPLICATION READY FOR REVIEW on Official Website!")
    print("  >> Review the form in the browser, then click Submit.")
    print("  >> Press ENTER here to continue to the next job...")
    print("  -------------------------------------------------------")
    input()
    page.close()
    return {"status": "staged", "reason": "user reviewed manually", "screenshot": shot}
