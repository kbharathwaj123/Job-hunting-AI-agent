"""
LinkedIn job search + Easy Apply.

FIRST RUN: a real browser window opens. Log into LinkedIn manually (solve
any captcha/2FA yourself). Your session is then saved in
data/browser_profile and reused on every future run — the script never
handles your password.

Default behavior (config.yaml -> sources.linkedin.auto_submit: false):
finds matching jobs, scores them, tailors your resume, fills the Easy
Apply form fields, and STOPS one click before final submit so you can
review. Flip auto_submit to true only once you trust it.
"""

from browser.session import human_delay, human_type
from browser.form_filler import fill_form_fields


def search_jobs(context, roles: list, locations: list, wfh_pref: str):
    page = context.new_page()
    results = []

    for role in roles:
        query = role.replace(" ", "%20")
        loc = locations[0] if locations else "Remote"
        url = f"https://www.linkedin.com/jobs/search/?keywords={query}&location={loc}"
        if wfh_pref in ("remote_only", "remote_or_hybrid"):
            url += "&f_WT=2"  # LinkedIn's remote filter

        page.goto(url)
        human_delay((4, 8))

        # Check we're actually logged in
        if "authwall" in page.url or page.locator("text=Sign in").count() > 0:
            print("[LOGIN REQUIRED] Not logged in to LinkedIn.")
            print("    A browser window is open -- please log into LinkedIn manually.")
            print("    ** DO NOT close the browser window or any tabs! **")
            print("    Once you are logged in and see your feed, press ENTER here to continue...")
            input()
            # User may have closed the tab, so open a fresh page
            try:
                page.goto(url)
            except Exception:
                page = context.new_page()
                page.goto(url)
            human_delay((4, 8))

        cards = page.locator("div.job-card-container").all()
        for card in cards[:25]:
            try:
                title = card.locator("a.job-card-list__title").inner_text()
                company = card.locator(".job-card-container__primary-description").inner_text()
                link = card.locator("a.job-card-list__title").get_attribute("href")
                results.append({
                    "source": "linkedin",
                    "title": title.strip(),
                    "company": company.strip(),
                    "url": f"https://www.linkedin.com{link}" if link.startswith("/") else link,
                })
            except Exception:
                continue

        human_delay((5, 10))

    page.close()
    return results


def easy_apply(context, job_url: str, resume_text: str, profile_answers: dict, tailored_summary: str, auto_submit: bool = False):
    """
    Opens a job, clicks Easy Apply, steps through multi-page modal, fills fields automatically,
    and either submits or leaves it open on the final review screen.
    """
    page = context.new_page()
    page.goto(job_url)
    human_delay((3, 6))

    easy_apply_btn = page.locator("button:has-text('Easy Apply')")
    if easy_apply_btn.count() == 0:
        page.close()
        return {"status": "skipped", "reason": "no Easy Apply button (external application)"}

    easy_apply_btn.first.click()
    human_delay((2, 4))

    # Stepping through the LinkedIn Easy Apply multi-page modal (up to 8 pages)
    for step in range(8):
        print(f"  [EASY APPLY] Processing step {step + 1} of form...")
        
        # 1. Fill fields on the current step modal
        fill_form_fields(page, resume_text, profile_answers)
        
        # 2. Check if we're at the final submission step
        submit_btn = page.locator("button:has-text('Submit application')")
        if submit_btn.count() > 0:
            if auto_submit:
                submit_btn.first.click()
                human_delay((2, 4))
                page.close()
                return {"status": "submitted"}
            else:
                break # stop at final review screen for manual review

        # 3. Check for Next / Review button to proceed
        next_btn = page.locator("button:has-text('Next'), button:has-text('Review')")
        if next_btn.count() > 0:
            next_btn.first.click()
            human_delay((2, 3))
        else:
            break

    if auto_submit:
        # If auto-submit was requested but the final submit button was not clicked/found
        page.close()
        return {"status": "staged", "reason": "Submit button not found"}

    # STAGED: keep page open for manual review
    print("  -------------------------------------------------------")
    print("  >> APPLICATION READY FOR REVIEW in the browser window!")
    print("  >> Review the form, then click 'Submit' in the browser.")
    print("  >> After submitting (or to skip), press ENTER here...")
    print("  -------------------------------------------------------")
    input()
    page.close()
    return {"status": "staged", "reason": "user reviewed manually"}
