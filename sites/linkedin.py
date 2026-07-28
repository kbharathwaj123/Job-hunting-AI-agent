"""
LinkedIn job search + Easy Apply with live progress logging and modal scoping.
"""

from browser.session import human_delay, human_type
from browser.form_filler import fill_form_fields
from browser.memory import memory


def search_jobs(context, roles: list, locations: list, wfh_pref: str):
    page = context.new_page()
    results = []

    for role in roles:
        query = role.replace(" ", "%20")
        loc = locations[0] if locations else "India"
        url = f"https://www.linkedin.com/jobs/search/?keywords={query}&location={loc}"
        
        if wfh_pref == "remote_only":
            url += "&f_WT=2"

        print(f"\n[LINKEDIN SEARCH] Role: '{role}' | Location: '{loc}'...")
        print(f"  Opening URL: {url[:85]}...")
        try:
            page.goto(url, timeout=25000)
            human_delay((3, 5))
        except Exception as e:
            print(f"  [LINKEDIN SEARCH ERROR] Could not load search page: {e}")
            continue

        # Check if logged in / authwall
        if "authwall" in page.url or page.locator("text=Sign in").count() > 0:
            print("[LOGIN REQUIRED] Not logged in to LinkedIn.")
            print("    Please log into LinkedIn manually in the browser window.")
            print("    Once logged in, press ENTER here to continue...")
            input()
            try:
                page.goto(url)
            except Exception:
                page = context.new_page()
                page.goto(url)
            human_delay((3, 5))

        card_selectors = [
            "div.job-card-container",
            "li.jobs-search-results__list-item",
            "div[data-job-id]",
            "div.job-card-list",
            "li.jobs-search-results-list__list-item"
        ]
        
        cards = []
        for sel in card_selectors:
            found = page.locator(sel).all()
            if len(found) > 0:
                cards = found
                break

        print(f"  [LINKEDIN] Extracted {len(cards)} candidate jobs on this page.")

        for idx, card in enumerate(cards[:25], 1):
            try:
                title_el = card.locator("a.job-card-list__title, a.job-card-container__link, a[data-control-name='job_card_click'], h3, strong")
                if title_el.count() == 0:
                    continue
                title = title_el.first.inner_text().strip()

                comp_el = card.locator(".job-card-container__primary-description, .job-card-container__company-name, span.job-card-container__primary-description, div.artdeco-entity-lockup__subtitle")
                company = comp_el.first.inner_text().strip() if comp_el.count() > 0 else "Company"

                link = title_el.first.get_attribute("href") or ""
                if link:
                    full_link = f"https://www.linkedin.com{link}" if link.startswith("/") else link
                    results.append({
                        "source": "linkedin",
                        "title": title,
                        "company": company,
                        "url": full_link
                    })
                    print(f"    -> Job {idx}: {title} @ {company}")
            except Exception:
                continue

        human_delay((2, 4))

    page.close()
    return results


def easy_apply(context, job_url: str, resume_text: str, profile_answers: dict, tailored_summary: str, auto_submit: bool = False, company_name: str = "LinkedIn"):
    """
    Opens a job page, locates Easy Apply, steps through the modal container, and fills fields live.
    """
    from browser.session import capture_confirmation_screenshot
    page = context.new_page()
    print(f"  [LINKEDIN APPLY] Navigating to: {job_url[:80]}...")
    try:
        page.goto(job_url, timeout=25000)
        human_delay((3, 5))
    except Exception as e:
        page.close()
        return {"status": "error", "reason": f"Could not load LinkedIn job: {e}"}

    # Locate Easy Apply button
    easy_apply_btn = page.locator("button:has-text('Easy Apply'), button.jobs-apply-button")
    if easy_apply_btn.count() == 0:
        print("  [LINKEDIN APPLY] No 'Easy Apply' button found (External company site listing).")
        page.close()
        return {"status": "skipped", "reason": "no Easy Apply button (external application)"}

    print("  [LINKEDIN APPLY] Found 'Easy Apply' button! Clicking to open modal...")
    try:
        easy_apply_btn.first.click()
        human_delay((2, 4))
    except Exception as e:
        page.close()
        return {"status": "error", "reason": f"Failed to click Easy Apply: {e}"}

    # Target the modal container for field filling
    modal = page.locator("div.jobs-easy-apply-modal, div.jobs-easy-apply-content, [role='dialog']")
    active_target = modal if modal.count() > 0 else page

    # Stepping through the LinkedIn Easy Apply multi-page modal (up to 8 pages)
    for step in range(8):
        print(f"  [LINKEDIN MODAL 📝] Step {step + 1}: Auto-filling input fields & screening questions...")
        
        # 1. Fill fields inside the modal container
        filled_count = fill_form_fields(active_target, resume_text, profile_answers)
        print(f"  [LINKEDIN MODAL 📝] Filled {filled_count} fields on Step {step + 1}.")
        
        # 2. Check for Submit button
        submit_btn = page.locator("button:has-text('Submit application'), button:has-text('Submit')")
        if submit_btn.count() > 0 and submit_btn.first.is_visible():
            print("  [LINKEDIN MODAL 🎯] Final 'Submit application' button detected!")
            if auto_submit:
                try:
                    submit_btn.first.click()
                    human_delay((3, 5))
                    shot = capture_confirmation_screenshot(page, company_name)
                    print("  [LINKEDIN SUCCESS 🎉] Application submitted successfully!")
                    page.close()
                    return {"status": "submitted", "screenshot": shot}
                except Exception as e:
                    print(f"  [LINKEDIN WARNING] Submit click error: {e}")
            else:
                break # stop for manual staging review

        # 3. Check for Next / Review button
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

    shot = capture_confirmation_screenshot(page, company_name)
    if auto_submit:
        page.close()
        return {"status": "submitted", "reason": "Completed Easy Apply steps", "screenshot": shot}

    print("  -------------------------------------------------------")
    print("  >> APPLICATION READY FOR REVIEW in the browser window!")
    print("  >> Review the form, then click 'Submit' in the browser.")
    print("  >> After submitting (or to skip), press ENTER here...")
    print("  -------------------------------------------------------")
    input()
    page.close()
    return {"status": "staged", "reason": "user reviewed manually", "screenshot": shot}
