"""
Naukri.com and Indeed automation — same persistent-login pattern as
linkedin.py. These are left as thinner skeletons since their DOM structure
changes more often than LinkedIn's; treat the selectors below as a
starting point to inspect-and-adjust in devtools when you first run this.
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
        page.goto(url)
        human_delay((4, 8))

        cards = page.locator("div.cust-job-tuple").all()
        for card in cards[:25]:
            try:
                title = card.locator("a.title").inner_text()
                company = card.locator("a.comp-name").inner_text()
                link = card.locator("a.title").get_attribute("href")
                results.append({"source": "naukri", "title": title.strip(),
                                 "company": company.strip(), "url": link})
            except Exception:
                continue
        human_delay((5, 10))
    page.close()
    return results


def search_indeed(context, roles: list, locations: list):
    page = context.new_page()
    results = []
    for role in roles:
        q = role.replace(" ", "+")
        loc = (locations[0] if locations else "").replace(" ", "+")
        url = f"https://www.indeed.com/jobs?q={q}&l={loc}"
        page.goto(url)
        human_delay((4, 8))

        cards = page.locator("div.job_seen_beacon").all()
        for card in cards[:25]:
            try:
                title = card.locator("h2 a").inner_text()
                company = card.locator("span.companyName").inner_text()
                link = card.locator("h2 a").get_attribute("href")
                results.append({"source": "indeed", "title": title.strip(),
                                 "company": company.strip(),
                                 "url": f"https://www.indeed.com{link}"})
            except Exception:
                continue
        human_delay((5, 10))
    page.close()
    return results




def apply_naukri(context, job_url: str, resume_text: str, profile_answers: dict,
                  resume_file_path: str, auto_submit: bool = False):
    page = context.new_page()
    page.goto(job_url)
    human_delay((3, 6))

    apply_btn = page.locator("button:has-text('Apply'), #apply-button")
    if apply_btn.count() == 0:
        page.close()
        return {"status": "skipped", "reason": "no Apply button found (may already be applied, or external)"}

    apply_btn.first.click()
    human_delay((2, 4))

    # Naukri sometimes opens a chatbot-style question flow instead of a
    # static form. Handle a few rounds of it.
    for _ in range(5):
        fill_form_fields(page, resume_text, profile_answers)
        next_btn = page.locator("button:has-text('Save and Continue'), button:has-text('Next')")
        if next_btn.count() > 0:
            next_btn.first.click()
            human_delay((2, 4))
        else:
            break

    if auto_submit:
        submit_btn = page.locator("button:has-text('Submit'), button:has-text('Send Application')")
        if submit_btn.count() > 0:
            submit_btn.first.click()
            human_delay((2, 4))
            page.close()
            return {"status": "submitted"}
        else:
            # If no extra submit button is found, clicking the main 'Apply' button was sufficient
            page.close()
            return {"status": "submitted"}

    # STAGED: keep page open for manual review
    print("  -------------------------------------------------------")
    print("  >> APPLICATION READY FOR REVIEW in the browser window!")
    print("  >> Review the form, then click 'Submit' in the browser.")
    print("  >> After submitting (or to skip), press ENTER here...")
    print("  -------------------------------------------------------")
    input()
    page.close()
    return {"status": "staged", "reason": "user reviewed manually"}


def apply_indeed(context, job_url: str, resume_text: str, profile_answers: dict,
                  resume_file_path: str, auto_submit: bool = False):
    page = context.new_page()
    page.goto(job_url)
    human_delay((3, 6))

    apply_btn = page.locator("button:has-text('Apply now'), a:has-text('Apply now')")
    if apply_btn.count() == 0:
        page.close()
        return {"status": "skipped", "reason": "no Indeed Apply button (likely redirects to external company site)"}

    apply_btn.first.click()
    human_delay((3, 5))

    # Indeed's own flow is multi-step (resume choice -> contact info ->
    # questions -> review). Step through it generically.
    for _ in range(6):
        # Resume upload step, if present
        file_input = page.locator("input[type='file']")
        if file_input.count() > 0 and resume_file_path:
            try:
                file_input.first.set_input_files(resume_file_path)
                human_delay((2, 3))
            except Exception:
                pass

        fill_form_fields(page, resume_text, profile_answers)

        continue_btn = page.locator("button:has-text('Continue'), button:has-text('Next')")
        if continue_btn.count() > 0:
            continue_btn.first.click()
            human_delay((2, 4))
        else:
            break

    if auto_submit:
        submit_btn = page.locator("button:has-text('Submit application'), button:has-text('Submit your application')")
        if submit_btn.count() > 0:
            submit_btn.first.click()
            human_delay((2, 4))
            page.close()
            return {"status": "submitted"}
        else:
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
