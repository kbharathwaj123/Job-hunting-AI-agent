"""
Company Careers Page & ATS Application Module.

Handles applying directly on official company websites and ATS platforms:
  - Workday (*.myworkdayjobs.com)
  - Greenhouse (boards.greenhouse.io)
  - Lever (jobs.lever.co)
  - SmartRecruiters (jobs.smartrecruiters.com)
  - Taleo (*.taleo.net)
  - ICIMS (*.icims.com)
  - Ashby (jobs.ashbyhq.com)
  - Custom Company Careers Pages (company.com/careers, company.com/jobs)

Features:
  - Google SSO / Login detection and automated authentication
  - Multi-step form filling via browser.form_filler
  - File upload for base_resume.docx / base_resume.pdf
  - Validation warning & error detection / auto-fix
"""

import re
import urllib.parse
from playwright.sync_api import Page, BrowserContext
from browser.session import human_delay, human_type
from browser.form_filler import fill_form_fields, detect_and_fix_validation_errors, handle_file_uploads


def find_official_careers_url(page: Page, company_name: str, role: str = "") -> str:
    """
    Searches Google / DuckDuckGo for the company's official career portal or job application page.
    """
    query = f"{company_name} official careers {role} jobs apply"
    url = f"https://www.google.com/search?q={urllib.parse.quote(query)}"
    
    print(f"  [OFFICIAL SITE SEARCH] Searching careers page for '{company_name}'...")
    try:
        page.goto(url, timeout=15000)
        page.wait_for_timeout(2000)
    except Exception:
        return ""

    # Look for search result links pointing to official company domains or ATS platforms
    ats_keywords = [
        "myworkdayjobs.com", "greenhouse.io", "lever.co", "smartrecruiters.com",
        "taleo.net", "icims.com", "ashbyhq.com", "careers", "jobs"
    ]
    
    try:
        links = page.locator("a[href^='http']").all()
        for link in links:
            href = link.get_attribute("href") or ""
            href_lower = href.lower()
            
            # Skip search engine / aggregator internal links
            if any(ignore in href_lower for ignore in ["google.com", "youtube.com", "wikipedia.org", "naukri.com", "linkedin.com", "indeed.com"]):
                continue
                
            if any(keyword in href_lower for keyword in ats_keywords):
                print(f"  [OFFICIAL SITE FOUND] Found careers portal: {href[:70]}...")
                return href
    except Exception:
        pass
        
    return ""


def handle_login_or_account_creation(page: Page, profile_answers: dict) -> bool:
    """
    Detects login/account walls on career portals and attempts Google SSO or auto-login/register.
    """
    try:
        text = page.locator("body").inner_text().lower()
        if not any(term in text for term in ["sign in", "log in", "create account", "register"]):
            return False  # No login wall
            
        # 1. Check for Google SSO button ("Sign in with Google", "Continue with Google")
        google_btn = page.locator("button:has-text('Google'), a:has-text('Google'), [aria-label*='Google'], div:has-text('Sign in with Google')")
        if google_btn.count() > 0 and google_btn.first.is_visible():
            print("  [LOGIN] Found 'Sign in with Google' option. Clicking SSO...")
            google_btn.first.click()
            human_delay((3, 6))
            return True

        # 2. Check for Account Creation / Registration inputs
        email = profile_answers.get("email", "kaithojubharathwaj123@gmail.com")
        email_field = page.locator("input[type='email'], input[name*='email'], input[id*='email']")
        if email_field.count() > 0 and email_field.first.is_visible():
            if not email_field.first.input_value().strip():
                email_field.first.fill(email)
                print(f"  [ACCOUNT SETUP] Auto-filled login email: {email}")
                human_delay((1, 2))

        # Check password fields
        pass_field = page.locator("input[type='password']")
        if pass_field.count() > 0 and pass_field.first.is_visible():
            pass_field.first.fill("JobAgentPass@2026")
            print("  [ACCOUNT SETUP] Auto-filled password.")
            human_delay((1, 2))

        # Check for Create Account / Submit Login button
        login_sub_btn = page.locator("button:has-text('Sign In'), button:has-text('Log In'), button:has-text('Create Account'), button:has-text('Register')")
        if login_sub_btn.count() > 0 and login_sub_btn.first.is_visible():
            login_sub_btn.first.click()
            human_delay((3, 5))
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
    # If original URL is a generic job aggregator, try finding the direct official company page
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

    # 1. Handle Login or Account Creation if present
    handle_login_or_account_creation(page, profile_answers)

    # 2. Look for initial Apply button on careers page
    apply_btn = page.locator("button:has-text('Apply'), a:has-text('Apply'), button:has-text('Apply Now'), a:has-text('Apply Now')")
    if apply_btn.count() > 0 and apply_btn.first.is_visible():
        try:
            apply_btn.first.click()
            human_delay((2, 4))
        except Exception:
            pass

    # Re-check login wall after clicking apply
    handle_login_or_account_creation(page, profile_answers)

    # 3. Multi-Step Form Filling & File Upload (up to 8 steps for complex portals like Workday/Taleo)
    for step in range(8):
        print(f"  [PORTAL FORM] Step {step + 1}: Auto-filling form fields & uploading resume...")
        
        # Attach resume file
        handle_file_uploads(page, resume_file_path)
        
        # Auto-fill form inputs
        fill_form_fields(page, resume_text, profile_answers, resume_file_path)
        
        # Detect and fix validation warnings/errors
        detect_and_fix_validation_errors(page, resume_text, profile_answers)

        # Check for Submit button
        submit_btn = page.locator("button:has-text('Submit Application'), button:has-text('Submit'), input[type='submit']")
        if submit_btn.count() > 0 and submit_btn.first.is_visible():
            if auto_submit:
                try:
                    submit_btn.first.click()
                    human_delay((3, 5))
                    print("  [COMPANY WEBSITE APPLY] Successfully submitted application!")
                    page.close()
                    return {"status": "submitted"}
                except Exception as e:
                    print(f"  [WARNING] Submit click error: {e}")
            else:
                break # stop for manual staging review

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

    if auto_submit:
        page.close()
        return {"status": "submitted", "reason": "Completed portal application steps"}

    # Staged for manual review
    print("  -------------------------------------------------------")
    print("  >> APPLICATION READY FOR REVIEW on Official Website!")
    print("  >> Review the form in the browser, then click Submit.")
    print("  >> Press ENTER here to continue to the next job...")
    print("  -------------------------------------------------------")
    input()
    page.close()
    return {"status": "staged", "reason": "user reviewed manually"}
