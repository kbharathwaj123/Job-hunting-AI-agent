"""
Naukri.com and Indeed automation with multi-selector fallback support.
"""

from browser.session import human_delay, human_type
from browser.form_filler import fill_form_fields
from resume.screening import answer_question


def search_naukri(context, roles: list, locations: list):
    page = context.new_page()
    results = []
    for role in roles:
        q = role.replace(" ", "-").lower()
        loc = (locations[0] if locations else "").lower()
        url = f"https://www.naukri.com/{q}-jobs-in-{loc}" if loc else f"https://www.naukri.com/{q}-jobs"
        
        print(f"  [NAUKRI SEARCH] Opening: {url[:80]}...")
        try:
            page.goto(url, timeout=25000)
            human_delay((4, 7))
        except Exception as e:
            print(f"  [NAUKRI SEARCH ERROR] {e}")
            continue

        card_selectors = [
            "div.cust-job-tuple",
            "article.jobTuple",
            "div.srp-job-tuple-header",
            "div.jobTuple",
            "div.tuple"
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
                title_el = card.locator("a.title, a.job-title, h2.title a")
                if title_el.count() == 0:
                    continue
                title = title_el.first.inner_text().strip()

                comp_el = card.locator("a.comp-name, a.subTitle, .comp-name, span.comp-name")
                company = comp_el.first.inner_text().strip() if comp_el.count() > 0 else "Company"

                link = title_el.first.get_attribute("href") or ""
                if link:
                    results.append({"source": "naukri", "title": title, "company": company, "url": link})
            except Exception:
                continue
        human_delay((3, 6))

    page.close()
    return results


def search_indeed(context, roles: list, locations: list):
    page = context.new_page()
    results = []
    for role in roles:
        q = role.replace(" ", "+")
        loc = (locations[0] if locations else "India").replace(" ", "+")
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


def apply_naukri(context, job_url: str, resume_text: str, profile_answers: dict,
                  resume_file_path: str, auto_submit: bool = False, company_name: str = "Naukri"):
    from browser.session import capture_confirmation_screenshot
    page = context.new_page()
    try:
        page.goto(job_url, timeout=25000)
        human_delay((3, 5))
    except Exception as e:
        page.close()
        return {"status": "error", "reason": f"Could not load Naukri job: {e}"}

    apply_btn = page.locator("button:has-text('Apply'), #apply-button, button.apply-button")
    if apply_btn.count() == 0:
        page.close()
        return {"status": "skipped", "reason": "no Apply button found (may already be applied, or external)"}

    try:
        apply_btn.first.click()
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

    shot = capture_confirmation_screenshot(page, company_name)
    if auto_submit:
        submit_btn = page.locator("button:has-text('Submit'), button:has-text('Send Application')")
        if submit_btn.count() > 0 and submit_btn.first.is_visible():
            try:
                submit_btn.first.click()
                human_delay((2, 4))
            except Exception:
                pass
        page.close()
        return {"status": "submitted", "screenshot": shot}

    print("  -------------------------------------------------------")
    print("  >> APPLICATION READY FOR REVIEW in the browser window!")
    print("  >> Review the form, then click 'Submit' in the browser.")
    print("  >> After submitting (or to skip), press ENTER here...")
    print("  -------------------------------------------------------")
    input()
    page.close()
    return {"status": "staged", "reason": "user reviewed manually", "screenshot": shot}


def apply_indeed(context, job_url: str, resume_text: str, profile_answers: dict,
                  resume_file_path: str, auto_submit: bool = False, company_name: str = "Indeed"):
    from browser.session import capture_confirmation_screenshot
    page = context.new_page()
    try:
        page.goto(job_url, timeout=25000)
        human_delay((3, 5))
    except Exception as e:
        page.close()
        return {"status": "error", "reason": f"Could not load Indeed job: {e}"}

    apply_btn = page.locator("button:has-text('Apply now'), a:has-text('Apply now'), #indeedApplyButton")
    if apply_btn.count() == 0:
        page.close()
        return {"status": "skipped", "reason": "no Indeed Apply button (likely redirects to external company site)"}

    try:
        apply_btn.first.click()
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

    shot = capture_confirmation_screenshot(page, company_name)
    if auto_submit:
        submit_btn = page.locator("button:has-text('Submit application'), button:has-text('Submit your application')")
        if submit_btn.count() > 0 and submit_btn.first.is_visible():
            try:
                submit_btn.first.click()
                human_delay((2, 4))
            except Exception:
                pass
        page.close()
        return {"status": "submitted", "screenshot": shot}

    print("  -------------------------------------------------------")
    print("  >> APPLICATION READY FOR REVIEW in the browser window!")
    print("  >> Review the form, then click 'Submit' in the browser.")
    print("  >> After submitting (or to skip), press ENTER here...")
    print("  -------------------------------------------------------")
    input()
    page.close()
    return {"status": "staged", "reason": "user reviewed manually", "screenshot": shot}
