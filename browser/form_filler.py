import re
import os
from pathlib import Path
from playwright.sync_api import Page
from browser.session import human_type, human_delay
from resume.screening import answer_question
from rapidfuzz import fuzz

def find_label_for_element(page, element) -> str:
    """Find a readable text label or description associated with an input element."""
    try:
        el_id = element.get_attribute("id")
        if el_id:
            label_el = page.locator(f"label[for='{el_id}']")
            if label_el.count() > 0:
                return label_el.first.inner_text().strip()
                
        parent = element.locator("xpath=..")
        if parent.count() > 0:
            parent_text = parent.first.inner_text().strip()
            lines = [l.strip() for l in parent_text.split('\n') if l.strip()]
            if lines:
                filtered = [l for l in lines if len(l) < 150 and not l.startswith('http')]
                if filtered:
                    return filtered[0]

        placeholder = element.get_attribute("placeholder")
        if placeholder:
            return placeholder.strip()
            
        aria_label = element.get_attribute("aria-label")
        if aria_label:
            return aria_label.strip()
            
        name = element.get_attribute("name")
        if name:
            return name.strip()
            
    except Exception:
        pass
    return ""


def select_best_option(select_element, question: str, resume_text: str, profile_answers: dict):
    """Pick the best option from a dropdown/select element based on screening logic."""
    try:
        options = select_element.locator("option").all()
        choices = []
        for opt in options:
            val = opt.get_attribute("value")
            text = opt.inner_text().strip()
            if val is not None and text and val != "" and "select" not in text.lower() and "choose" not in text.lower():
                choices.append(text)
                
        if not choices:
            return None
            
        ideal_answer = answer_question(question, resume_text, profile_answers)
        if not ideal_answer:
            return choices[0]
            
        for choice in choices:
            if choice.lower() in ideal_answer.lower() or ideal_answer.lower() in choice.lower():
                return choice
                
        best_choice = None
        best_score = 0
        for choice in choices:
            score = fuzz.token_sort_ratio(choice.lower(), ideal_answer.lower())
            if score > best_score:
                best_score = score
                best_choice = choice
                
        if best_score >= 40:
            return best_choice
            
        return choices[0]
    except Exception:
        return None


def resolve_valid_resume_path(resume_file_path: str = "") -> str:
    """Resolves a valid existing resume file path from config or defaults."""
    candidates = [
        resume_file_path,
        "c:/projects/job-agent/data/Bharathwaj_Kaithoju_v2.pdf",
        "c:/projects/job-agent/data/Bharathwaj_Kaithoju_v2.docx",
        "c:/projects/job-agent/data/Bharathwaj_Kaithoju_Resume_Updated.pdf",
        "c:/projects/job-agent/data/Bharathwaj_Kaithoju_Resume_Updated.docx",
        "c:/projects/job-agent/data/base_resume.pdf",
        "c:/projects/job-agent/data/base_resume.docx",
    ]
    for c in candidates:
        if c and os.path.exists(c):
            return str(Path(c).resolve())
    return ""


def handle_file_uploads(page: Page, resume_file_path: str = "") -> int:
    """
    Mandatory Resume Upload: Finds all input[type='file'] (Resume/CV uploads)
    or file upload buttons and attaches the candidate's resume.
    """
    valid_path = resolve_valid_resume_path(resume_file_path)
    if not valid_path:
        print("  [RESUME WARNING ⚠️] No valid resume file found locally!")
        return 0

    uploaded = 0
    try:
        # 1. Direct input[type='file'] elements
        file_inputs = page.locator("input[type='file']").all()
        for file_input in file_inputs:
            try:
                file_input.set_input_files(valid_path)
                print(f"  [MANDATORY RESUME UPLOAD 📄] Attached resume file: {os.path.basename(valid_path)}")
                uploaded += 1
                human_delay((1, 3))
            except Exception:
                continue

        # 2. Clickable "Upload Resume" or "Attach Resume" buttons that trigger file choosers
        if uploaded == 0:
            upload_btns = page.locator("button:has-text('Upload'), button:has-text('Attach'), a:has-text('Upload Resume'), label:has-text('Upload')").all()
            for btn in upload_btns:
                try:
                    if btn.is_visible():
                        with page.expect_file_chooser(timeout=3000) as fc_info:
                            btn.click()
                        file_chooser = fc_info.value
                        file_chooser.set_files(valid_path)
                        print(f"  [MANDATORY RESUME UPLOAD 📄] Attached resume via upload button: {os.path.basename(valid_path)}")
                        uploaded += 1
                        human_delay((1, 3))
                        break
                except Exception:
                    continue

        # 3. Radio selection for saved resumes (e.g. LinkedIn / Indeed saved resume)
        saved_resume_radios = page.locator("input[type='radio'][value*='resume'], input[type='radio'][id*='resume']").all()
        for radio in saved_resume_radios:
            try:
                if not radio.is_checked():
                    radio.check()
                    print("  [MANDATORY RESUME SELECTION 📄] Selected saved resume profile.")
                    uploaded += 1
            except Exception:
                continue

    except Exception as e:
        print(f"  [RESUME UPLOAD ERROR] {e}")

    return uploaded


def fill_form_fields(page: Page, resume_text: str, profile_answers: dict, resume_file_path: str = "", max_fields: int = 25):
    """
    Scans page for form inputs (text, tel, email, select, radio, checkbox, file upload),
    matches against resume/profile answers, enforces MANDATORY RESUME ATTACHMENT, and fills fields live.
    """
    filled_count = 0
    
    # 0. MANDATORY RESUME ATTACHMENT / SELECTION
    filled_count += handle_file_uploads(page, resume_file_path)

    # 1. Handle Text, Number, Email, Tel, and Textarea inputs
    text_inputs = page.locator("input[type='text'], input[type='number'], input[type='tel'], input[type='email'], input:not([type]), textarea").all()
    for field in text_inputs:
        if filled_count >= max_fields:
            break
        try:
            if not field.is_visible() or field.is_disabled():
                continue
            val = field.input_value().strip()
            if val:
                continue
                
            label = find_label_for_element(page, field)
            if not label:
                continue
                
            answer = answer_question(label, resume_text, profile_answers)
            if answer:
                field_type = field.get_attribute("type") or ""
                if field_type.lower() == "tel" or "phone" in label.lower() or "mobile" in label.lower():
                    digits = re.sub(r'[^\d]', '', str(answer))
                    if len(digits) >= 10:
                        answer = digits[-10:]
                elif field_type.lower() in ("number", "numeric") or "years" in label.lower() or "experience" in label.lower() or "how many" in label.lower():
                    digits = re.sub(r'[^\d]', '', str(answer))
                    answer = digits if digits else "3"
                        
                field.click()
                human_delay((0.3, 0.8))
                field.fill(str(answer))
                print(f"  [AUTO-FILL] Field '{label[:35]}' -> '{answer}'")
                filled_count += 1
                human_delay((0.8, 1.8))
        except Exception:
            continue

    # 2. Handle Select / Dropdown elements & ARIA Comboboxes
    select_elements = page.locator("select").all()
    for select in select_elements:
        if filled_count >= max_fields:
            break
        try:
            if not select.is_visible() or select.is_disabled():
                continue
            label = find_label_for_element(page, select)
            
            best_opt = select_best_option(select, label, resume_text, profile_answers) if label else None
            if best_opt:
                select.select_option(label=best_opt)
                print(f"  [AUTO-FILL] Dropdown '{label[:35]}' -> Selected '{best_opt}'")
                filled_count += 1
                human_delay((0.8, 1.8))
            else:
                # Mandatory dropdown fallback for required fields
                is_req = select.get_attribute("required") is not None or select.get_attribute("aria-required") == "true" or "*" in label
                opts = select.locator("option").all()
                if is_req and len(opts) > 1:
                    select.select_option(index=1)
                    print(f"  [AUTO-FILL MANDATORY ⚠️] Required Dropdown '{label[:35]}' -> Selected Option 1")
                    filled_count += 1
                    human_delay((0.5, 1))
        except Exception:
            continue

    # 2b. Handle ARIA Comboboxes / Listboxes (Workday, Greenhouse, Lever custom dropdowns)
    aria_dropdowns = page.locator("div[role='combobox'], button[aria-haspopup='listbox'], div[role='listbox']").all()
    for combo in aria_dropdowns:
        if filled_count >= max_fields:
            break
        try:
            if not combo.is_visible() or combo.is_disabled():
                continue
            lbl = find_label_for_element(page, combo)
            combo.click()
            human_delay((0.4, 0.8))
            
            opts = page.locator("li[role='option'], div[role='option'], [role='treeitem']").all()
            if opts:
                opts[0].click()
                print(f"  [AUTO-FILL ARIA] Dropdown '{lbl[:30]}' -> Clicked Option 1")
                filled_count += 1
                human_delay((0.5, 1))
        except Exception:
            continue

    # 3. Handle Radio Groups
    seen_groups = set()
    radio_inputs = page.locator("input[type='radio']").all()
    for radio in radio_inputs:
        if filled_count >= max_fields:
            break
        try:
            name = radio.get_attribute("name")
            if not name or name in seen_groups:
                continue
            seen_groups.add(name)
            
            group = page.locator(f"input[type='radio'][name='{name}']")
            if group.locator(":checked").count() > 0:
                continue
                
            question_text = ""
            container = radio.locator("xpath=ancestor::fieldset[1]")
            if container.count() > 0:
                question_text = container.first.inner_text().strip()
            if not question_text:
                question_text = find_label_for_element(page, radio) or name
                
            answer = answer_question(question_text, resume_text, profile_answers)
            if not answer:
                continue
                
            options = group.all()
            picked = False
            for opt in options:
                opt_id = opt.get_attribute("id")
                opt_text = ""
                if opt_id:
                    lbl = page.locator(f"label[for='{opt_id}']")
                    if lbl.count() > 0:
                        opt_text = lbl.first.inner_text().strip()
                if opt_text and (opt_text.lower() in answer.lower() or answer.lower() in opt_text.lower()):
                    opt.check()
                    print(f"  [AUTO-FILL] Radio '{question_text[:30]}...' -> Checked '{opt_text}'")
                    picked = True
                    break
            if not picked and options:
                options[0].check()
                picked_lbl = ""
                opt_id = options[0].get_attribute("id")
                if opt_id:
                    lbl = page.locator(f"label[for='{opt_id}']")
                    if lbl.count() > 0:
                        picked_lbl = lbl.first.inner_text().strip()
                print(f"  [AUTO-FILL] Radio '{question_text[:30]}...' -> Fallback Checked '{picked_lbl or 'Option 1'}'")
                
            filled_count += 1
            human_delay((0.8, 1.8))
        except Exception:
            continue

    # 4. Handle Checkboxes
    checkboxes = page.locator("input[type='checkbox']").all()
    for cb in checkboxes:
        try:
            if not cb.is_visible() or cb.is_disabled() or cb.is_checked():
                continue
            
            cb_label = find_label_for_element(page, cb).lower()
            check_it = False
            if any(term in cb_label for term in ["agree", "accept", "terms", "policy", "declaration", "consent"]):
                check_it = True
            elif any(term in cb_label for term in ["authorize", "work in", "eligib"]):
                ans = answer_question(cb_label, resume_text, profile_answers).lower()
                if "yes" in ans or "true" in ans or "authorize" in ans:
                    check_it = True
                    
            if check_it:
                cb.check()
                print(f"  [AUTO-FILL] Checkbox '{cb_label[:30]}...' -> Checked")
                human_delay((0.5, 1))
        except Exception:
            continue

    return filled_count


def detect_and_fix_validation_errors(page: Page, resume_text: str, profile_answers: dict) -> int:
    """
    Analyzes page for validation errors/warnings, re-enforces mandatory resume attachment,
    resolves missing inputs, and returns fixed count.
    """
    fixed_count = 0
    try:
        # Mandatory resume re-check if error relates to missing CV/Resume
        file_inputs = page.locator("input[type='file']").all()
        for fi in file_inputs:
            if fi.is_visible() and fi.evaluate("el => el.files.length === 0"):
                fixed_count += handle_file_uploads(page)

        invalid_fields = page.locator("[aria-invalid='true'], input.error, input.is-invalid, select.error, select.is-invalid, textarea.error").all()
        for field in invalid_fields:
            if not field.is_visible() or field.is_disabled():
                continue
            label = find_label_for_element(page, field)
            tag_name = field.evaluate("el => el.tagName.toLowerCase()")
            
            if tag_name == "select":
                opts = field.locator("option").all()
                if len(opts) > 1:
                    field.select_option(index=1)
                    print(f"  [FIX-ERROR] Re-selected dropdown option for '{label[:30]}'")
                    fixed_count += 1
            else:
                ans = answer_question(label, resume_text, profile_answers) or "Yes"
                field.click()
                field.fill(str(ans))
                print(f"  [FIX-ERROR] Re-filled required field '{label[:30]}' -> '{ans}'")
                fixed_count += 1
                
        error_msgs = page.locator(".error-message, .invalid-feedback, .validation-error, .alert-danger, [role='alert']").all()
        for msg in error_msgs:
            if msg.is_visible():
                txt = msg.inner_text().strip()
                if txt:
                    print(f"  [WARNING DETECTED] Page form error: '{txt[:60]}'")
                    extra_fills = fill_form_fields(page, resume_text, profile_answers)
                    if extra_fills > 0:
                        fixed_count += extra_fills
                        
    except Exception:
        pass
    return fixed_count
