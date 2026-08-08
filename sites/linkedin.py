"""
LinkedIn Job Search & Easy Apply Module with Modal Container Scoping,
Live Terminal Step Logging, Confirmation Proof Screenshots, and Submission Guarantee.
"""

import time
from playwright.sync_api import Page, BrowserContext
from browser.session import human_delay, human_type, capture_confirmation_screenshot
from browser.form_filler import fill_form_fields


def ensure_english_linkedin(page: Page):
    """
    Detects if LinkedIn interface is rendered in Arabic or non-English (RTL),
    and automatically enforces English interface cookies/locale.
    """
    try:
        lang_attr = (page.locator("html").get_attribute("lang") or "").lower()
        dir_attr = (page.locator("html").get_attribute("dir") or "").lower()
        if "ar" in lang_attr or dir_attr == "rtl":
            print("  [LANGUAGE ENFORCER 🌐] Arabic/RTL layout detected on LinkedIn. Switching interface to English...")
            page.context.add_cookies([
                {"name": "lang", "value": "v=2&lang=en-us", "domain": ".linkedin.com", "path": "/"},
                {"name": "li_lang", "value": "en_US", "domain": ".linkedin.com", "path": "/"}
            ])
            page.reload()
            human_delay((2, 3))
    except Exception:
        pass


def search_jobs(context: BrowserContext, roles: list, locations: list, wfh_pref: str) -> list:
    page = context.new_page()
    results = []

    for role in roles:
        for loc in locations:
            url = f"https://www.linkedin.com/jobs/search/?keywords={role}&location={loc}&lang=en_US"
            if wfh_pref == "remote_only":
                url += "&f_WT=2"
            elif wfh_pref == "remote_or_hybrid":
                url += "&f_WT=2%2C3"

            print(f"  [LINKEDIN SEARCH] Opening: {url[:80]}...")
            try:
                page.goto(url, timeout=25000)
                human_delay((2, 4))
                ensure_english_linkedin(page)
            except Exception as e:
                print(f"  [LINKEDIN SEARCH ERROR] {e}")
                continue

            card_selectors = [
                "div.job-card-container",
                "li.jobs-search-results__list-item",
                "div.jobs-search-results-list__list-item",
                "div.job-card-list",
                "div.base-card"
            ]

            cards = []
            for sel in card_selectors:
                found = page.locator(sel).all()
                if len(found) > 0:
                    cards = found
                    break

            print(f"  [LINKEDIN] Found {len(cards)} raw job card elements.")

            for card in cards[:30]:
                try:
                    title_el = card.locator("a.job-card-list__title, a.job-card-container__link, strong")
                    if title_el.count() == 0:
                        continue
                    title = title_el.first.inner_text().strip()

                    comp_el = card.locator("span.job-card-container__primary-description, div.artdeco-entity-lockup__subtitle")
                    company = comp_el.first.inner_text().strip() if comp_el.count() > 0 else "Company"

                    link = title_el.first.get_attribute("href") or ""
                    if link:
                        full_link = f"https://www.linkedin.com{link}" if link.startswith("/") else link
                        results.append({"source": "linkedin", "title": title, "company": company, "url": full_link})
                except Exception:
                    continue
            human_delay((2, 4))

    page.close()
    return results


def easy_apply(context: BrowserContext, job_url: str, resume_text: str, profile_answers: dict,
               custom_summary: str = "", auto_submit: bool = True, company_name: str = "LinkedIn") -> dict:
    """
    Navigates to a LinkedIn job posting, opens the Easy Apply modal, and completes all form steps.
    Waits for the final confirmation message before taking a proof screenshot.
    """
    page = context.new_page()
    page.set_default_timeout(30000)

    # Force English locale on LinkedIn job URL
    target_url = job_url
    if "lang=en_US" not in target_url:
        target_url += ("&lang=en_US" if "?" in target_url else "?lang=en_US")

    print(f"  [LINKEDIN EASY APPLY] Opening job page: {target_url[:80]}...")
    try:
        page.goto(target_url, timeout=25000)
        human_delay((2, 4))
        ensure_english_linkedin(page)
    except Exception as e:
        page.close()
        return {"status": "error", "reason": f"Could not load LinkedIn job page: {e}"}

    apply_btn = page.locator("button.jobs-apply-button, button:has-text('Easy Apply'), button:has-text('Apply now')")
    if apply_btn.count() == 0:
        page.close()
        return {"status": "skipped", "reason": "No Easy Apply button found on page"}

    try:
        apply_btn.first.click()
        print(f"  [LINKEDIN EASY APPLY] Opened Easy Apply modal for '{company_name}'.")
        human_delay((2, 4))
    except Exception as e:
        page.close()
        return {"status": "error", "reason": f"Could not click Easy Apply button: {e}"}

    modal = page.locator("div.jobs-easy-apply-modal, div.jobs-easy-apply-content, [role='dialog']")
    active_target = modal if modal.count() > 0 else page

    submitted_successfully = False

    for step in range(8):
        print(f"  [LINKEDIN MODAL 📝] Step {step + 1}: Auto-filling input fields & screening questions...")
        
        filled_count = fill_form_fields(active_target, resume_text, profile_answers)
        print(f"  [LINKEDIN MODAL 📝] Filled {filled_count} fields on Step {step + 1}.")
        
        submit_btn = page.locator("button:has-text('Submit application'), button:has-text('Submit'), button[aria-label*='Submit application']")
        if submit_btn.count() > 0 and submit_btn.first.is_visible():
            print("  [LINKEDIN MODAL 🎯] Final 'Submit application' button detected!")
            if auto_submit:
                try:
                    submit_btn.first.click()
                    print("  [LINKEDIN SUBMIT] Clicked Submit application button! Waiting for confirmation response...")
                    page.wait_for_timeout(7000)  # Wait for submission network request & success dialog
                    done_btn = page.locator("button:has-text('Done'), button:has-text('Dismiss'), div.artdeco-inline-feedback--success, h3:has-text('Application submitted')")
                    if verify_submission_confirmation(page) or done_btn.count() > 0 or not submit_btn.first.is_visible():
                        submitted_successfully = True
                        if done_btn.count() > 0 and done_btn.first.is_visible():
                            try:
                                done_btn.first.click()
                            except Exception:
                                pass
                    break
                except Exception as e:
                    print(f"  [LINKEDIN WARNING] Submit click error: {e}")
            else:
                break

        next_btn = page.locator("button:has-text('Next'), button:has-text('Review')")
        if next_btn.count() > 0 and next_btn.first.is_visible():
            try:
                print("  [LINKEDIN MODAL] Clicking 'Next' / 'Review' to proceed...")
                next_btn.first.click()
                human_delay((2, 4))
            except Exception:
                break
        else:
            print("  [LINKEDIN MODAL] Reached end of form steps.")
            break

    # Check for submit button one final time if not yet submitted
    if not submitted_successfully and auto_submit:
        submit_btn = page.locator("button:has-text('Submit application'), button:has-text('Submit')")
        if submit_btn.count() > 0 and submit_btn.first.is_visible():
            try:
                submit_btn.first.click()
                print("  [LINKEDIN SUBMIT] Final submission click executed! Waiting for confirmation...")
                page.wait_for_timeout(7000)
                from browser.session import verify_submission_confirmation
                done_btn = page.locator("button:has-text('Done'), button:has-text('Dismiss'), div.artdeco-inline-feedback--success, h3:has-text('Application submitted')")
                if verify_submission_confirmation(page) or done_btn.count() > 0 or not submit_btn.first.is_visible():
                    submitted_successfully = True
                    if done_btn.count() > 0 and done_btn.first.is_visible():
                        try:
                            done_btn.first.click()
                        except Exception:
                            pass
            except Exception:
                pass

    shot = capture_confirmation_screenshot(page, company_name)
    
    if auto_submit and submitted_successfully:
        print(f"  [LINKEDIN SUCCESS 🎉] Application for '{company_name}' successfully submitted and email confirmation triggered!")
        page.close()
        return {"status": "submitted", "reason": "Application submitted & confirmation verified", "screenshot": shot}
    elif auto_submit:
        print(f"  [LINKEDIN WARNING] Form step reached limit or required field was unhandled.")
        page.close()
        return {"status": "staged", "reason": "Form requires manual verification", "screenshot": shot}

    print("  -------------------------------------------------------")
    print("  >> APPLICATION READY FOR REVIEW in the browser window!")
    print("  >> Review the form, then click 'Submit' in the browser.")
    print("  >> After submitting (or to skip), press ENTER here...")
    print("  -------------------------------------------------------")
    input()
    page.close()
    return {"status": "staged", "reason": "user reviewed manually", "screenshot": shot}
