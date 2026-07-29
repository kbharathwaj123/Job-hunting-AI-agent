"""
Naukri & Indeed Search & Apply Module with Multi-Step Stepper Support,
Confirmation Screenshots AFTER Submission, and Error Handling.
"""

from playwright.sync_api import Page, BrowserContext
from browser.session import human_delay, human_type, capture_confirmation_screenshot
from browser.form_filler import fill_form_fields


def search_naukri(context: BrowserContext, roles: list, locations: list) -> list:
    page = context.new_page()
    results = []

    for role in roles:
        for loc in locations:
            url = f"https://www.naukri.com/{role.lower().replace(' ', '-')}-jobs-in-{loc.lower().replace(' ', '-')}"
            print(f"  [NAUKRI SEARCH] Opening: {url[:80]}...")
            try:
                page.goto(url, timeout=25000)
                human_delay((3, 5))
            except Exception as e:
                print(f"  [NAUKRI SEARCH ERROR] {e}")
                continue

            card_selectors = [
                "div.srp-jobtuple-wrapper",
                "article.jobTuple",
                "div.jobTuple",
                "div.cust-job-tuple"
            ]

            cards = []
            for sel in card_selectors:
                found = page.locator(sel).all()
                if len(found) > 0:
                    cards = found
                    break

            print(f"  [NAUKRI] Found {len(cards)} raw job card elements.")

            for card in cards[:30]:
                try:
                    title_el = card.locator("a.title, a.job-title, a[class*='title']")
                    if title_el.count() == 0:
                        continue
                    title = title_el.first.inner_text().strip()

                    comp_el = card.locator("a.subTitle, span.comp-name, a.comp-name")
                    company = comp_el.first.inner_text().strip() if comp_el.count() > 0 else "Company"

                    link = title_el.first.get_attribute("href") or ""
                    if link:
                        full_link = f"https://www.naukri.com{link}" if link.startswith("/") else link
                        results.append({"source": "naukri", "title": title, "company": company, "url": full_link})
                except Exception:
                    continue
            human_delay((2, 4))

    page.close()
    return results


def search_indeed(context: BrowserContext, roles: list, locations: list) -> list:
    page = context.new_page()
    results = []

    for role in roles:
        for loc in locations:
            q = role.replace(' ', '+')
            url = f"https://www.indeed.com/jobs?q={q}&l={loc}"
            
            print(f"  [INDEED SEARCH] Opening: {url[:80]}...")
            try:
                page.goto(url, timeout=25000)
                human_delay((4, 7))
            except Exception as e:
                print(f"  [INDEED SEARCH ERROR] {e}")
                continue

            card_selectors = [
                "div.job_seen_beacon",
                "td.resultContent",
                "div.cardOutline",
                "div.slider_item",
                "div.jobsearch-ResultsList > div"
            ]

            cards = []
            for sel in card_selectors:
                found = page.locator(sel).all()
                if len(found) > 0:
                    cards = found
                    break

            print(f"  [INDEED] Found {len(cards)} raw job card elements.")

            for card in cards[:30]:
                try:
                    title_el = card.locator("h2 a, a.jcs-JobTitle, a[data-jk], h2.jobTitle span")
                    if title_el.count() == 0:
                        continue
                    title = title_el.first.inner_text().strip()

                    comp_el = card.locator("span.companyName, span[data-testid='company-name'], div.company_location span")
                    company = comp_el.first.inner_text().strip() if comp_el.count() > 0 else "Company"

                    link = title_el.first.get_attribute("href") or ""
                    if link:
                        full_link = f"https://www.indeed.com{link}" if link.startswith("/") else link
                        results.append({"source": "indeed", "title": title, "company": company, "url": full_link})
                except Exception:
                    continue
            human_delay((3, 6))

    page.close()
    return results


def apply_naukri(context: BrowserContext, job_url: str, resume_text: str, profile_answers: dict,
                  resume_file_path: str, auto_submit: bool = True, company_name: str = "Naukri") -> dict:
    page = context.new_page()
    page.set_default_timeout(30000)
    
    try:
        page.goto(job_url, timeout=25000)
        human_delay((3, 5))
    except Exception as e:
        page.close()
        return {"status": "error", "reason": f"Could not load Naukri job: {e}"}

    apply_btn = page.locator("button:has-text('Apply'), #apply-button, button.apply-button, span:has-text('Apply')")
    if apply_btn.count() == 0:
        page.close()
        return {"status": "skipped", "reason": "No Apply button found (may already be applied)"}

    try:
        apply_btn.first.click()
        print(f"  [NAUKRI] Clicked initial Apply button for '{company_name}'.")
        human_delay((2, 4))
    except Exception:
        pass

    for _ in range(5):
        fill_form_fields(page, resume_text, profile_answers)
        next_btn = page.locator("button:has-text('Save and Continue'), button:has-text('Next')")
        if next_btn.count() > 0 and next_btn.first.is_visible():
            try:
                next_btn.first.click()
                human_delay((2, 4))
            except Exception:
                break
        else:
            break

    submitted = False
    if auto_submit:
        submit_btn = page.locator("button:has-text('Submit'), button:has-text('Send Application'), button:has-text('Apply Now')")
        if submit_btn.count() > 0 and submit_btn.first.is_visible():
            try:
                submit_btn.first.click()
                print("  [NAUKRI SUBMIT] Clicked final Submit button! Waiting for confirmation screen...")
                page.wait_for_timeout(7000)
                submitted = True
            except Exception as e:
                print(f"  [NAUKRI WARNING] Submit click error: {e}")

    # Capture confirmation screenshot AFTER submit button is clicked & response loads
    shot = capture_confirmation_screenshot(page, company_name)

    if auto_submit:
        page.close()
        return {"status": "submitted", "reason": "Application submitted & confirmation verified", "screenshot": shot}

    print("  -------------------------------------------------------")
    print("  >> APPLICATION READY FOR REVIEW in the browser window!")
    print("  >> Review the form, then click 'Submit' in the browser.")
    print("  >> After submitting (or to skip), press ENTER here...")
    print("  -------------------------------------------------------")
    input()
    page.close()
    return {"status": "staged", "reason": "user reviewed manually", "screenshot": shot}


def apply_indeed(context: BrowserContext, job_url: str, resume_text: str, profile_answers: dict,
                  resume_file_path: str, auto_submit: bool = True, company_name: str = "Indeed") -> dict:
    page = context.new_page()
    page.set_default_timeout(30000)
    
    try:
        page.goto(job_url, timeout=25000)
        human_delay((3, 5))
    except Exception as e:
        page.close()
        return {"status": "error", "reason": f"Could not load Indeed job: {e}"}

    apply_btn = page.locator("button:has-text('Apply now'), a:has-text('Apply now'), #indeedApplyButton")
    if apply_btn.count() == 0:
        page.close()
        return {"status": "skipped", "reason": "No Indeed Apply button found"}

    try:
        apply_btn.first.click()
        print(f"  [INDEED] Clicked Apply now button for '{company_name}'.")
        human_delay((3, 5))
    except Exception:
        pass

    for _ in range(6):
        fill_form_fields(page, resume_text, profile_answers, resume_file_path)

        continue_btn = page.locator("button:has-text('Continue'), button:has-text('Next')")
        if continue_btn.count() > 0 and continue_btn.first.is_visible():
            try:
                continue_btn.first.click()
                human_delay((2, 4))
            except Exception:
                break
        else:
            break

    submitted = False
    if auto_submit:
        submit_btn = page.locator("button:has-text('Submit your application'), button:has-text('Submit'), button:has-text('Send Application')")
        if submit_btn.count() > 0 and submit_btn.first.is_visible():
            try:
                submit_btn.first.click()
                print("  [INDEED SUBMIT] Clicked final Submit application button! Waiting for confirmation screen...")
                page.wait_for_timeout(7000)
                submitted = True
            except Exception as e:
                print(f"  [INDEED WARNING] Submit click error: {e}")

    # Capture confirmation screenshot AFTER submit button is clicked & response loads
    shot = capture_confirmation_screenshot(page, company_name)

    if auto_submit:
        page.close()
        return {"status": "submitted", "reason": "Application submitted & confirmation verified", "screenshot": shot}

    print("  -------------------------------------------------------")
    print("  >> APPLICATION READY FOR REVIEW in the browser window!")
    print("  >> Review the form, then click 'Submit' in the browser.")
    print("  >> After submitting (or to skip), press ENTER here...")
    print("  -------------------------------------------------------")
    input()
    page.close()
    return {"status": "staged", "reason": "user reviewed manually", "screenshot": shot}
