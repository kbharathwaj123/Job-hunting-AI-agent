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
        # 1. Look for <label> tag with 'for' matching the element's id
        el_id = element.get_attribute("id")
        if el_id:
            label_el = page.locator(f"label[for='{el_id}']")
            if label_el.count() > 0:
                return label_el.first.inner_text().strip()
                
        # 2. Check parent element or adjacent labels
        parent = element.locator("xpath=..")
        if parent.count() > 0:
            parent_text = parent.first.inner_text().strip()
            # If the parent text is reasonably short, it's likely the question/label
            lines = [l.strip() for l in parent_text.split('\n') if l.strip()]
            if lines:
                # filter out input element contents
                filtered = [l for l in lines if len(l) < 150 and not l.startswith('http')]
                if filtered:
                    return filtered[0]

        # 3. Check placeholder, aria-label, name attributes
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
            
        # Get the targeted answer based on the question
        ideal_answer = answer_question(question, resume_text, profile_answers)
        if not ideal_answer:
            return choices[0]
            
        # 1. Direct substring check
        for choice in choices:
            if choice.lower() in ideal_answer.lower() or ideal_answer.lower() in choice.lower():
                return choice
                
        # 2. Fuzzy matching score
        best_choice = None
        best_score = 0
        for choice in choices:
            score = fuzz.token_sort_ratio(choice.lower(), ideal_answer.lower())
            if score > best_score:
                best_score = score
                best_choice = choice
                
        if best_score >= 40:
            return best_choice
            
        return choices[0]  # fallback to first valid option
    except Exception:
        return None


def handle_file_uploads(page: Page, resume_file_path: str = "") -> int:
    """Finds input[type='file'] (Resume/CV uploads) and attaches the user's resume."""
    if not resume_file_path or not os.path.exists(resume_file_path):
        # Fallback to default base_resume.docx if path not provided
        default_path = Path("c:/projects/job-agent/data/base_resume.docx")
        if default_path.exists():
            resume_file_path = str(default_path)
        else:
            return 0
            
    uploaded = 0
    try:
        file_inputs = page.locator("input[type='file']").all()
        for file_input in file_inputs:
            try:
                # Set the input files
                file_input.set_input_files(resume_file_path)
                print(f"  [RESUME UPLOAD] Attached resume: {os.path.basename(resume_file_path)}")
                uploaded += 1
                human_delay((1, 3))
            except Exception as e:
                # Try setting via page event handler if direct fails
                continue
    except Exception:
        pass
    return uploaded


def fill_form_fields(page: Page, resume_text: str, profile_answers: dict, resume_file_path: str = "", max_fields: int = 25):
    """
    Scans the page for common form inputs (text, tel, email, select, radio, checkbox, file upload),
    matches them against resume/profile answers, and fills them in automatically.
    """
    filled_count = 0
    
    # 0. Handle File Uploads (Resume / CV)
    if resume_file_path or os.path.exists("c:/projects/job-agent/data/base_resume.docx"):
        filled_count += handle_file_uploads(page, resume_file_path)

    # 1. Handle Text, Number, Email, Tel, and Textarea inputs
    text_inputs = page.locator("input[type='text'], input[type='number'], input[type='tel'], input[type='email'], input:not([type]), textarea").all()
    for field in text_inputs:
        if filled_count >= max_fields:
            break
        try:
            # Skip hidden, disabled, or already filled fields
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
                # Clean phone format if tel field
                field_type = field.get_attribute("type") or ""
                if field_type.lower() == "tel" or "phone" in label.lower() or "mobile" in label.lower():
                    # extract digits
                    digits = re.sub(r'[^\d]', '', str(answer))
                    if len(digits) >= 10:
                        answer = digits[-10:]  # 10-digit clean mobile number
                        
                field.click()
                human_delay((0.3, 0.8))
                human_type(field, str(answer))
                print(f"  [AUTO-FILL] Field '{label[:35]}' -> '{answer}'")
                filled_count += 1
                human_delay((0.8, 2.0))
        except Exception:
            continue

    # 2. Handle Select / Dropdown elements
    select_elements = page.locator("select").all()
    for select in select_elements:
        if filled_count >= max_fields:
            break
        try:
            if not select.is_visible() or select.is_disabled():
                continue
            label = find_label_for_element(page, select)
            if not label:
                continue
                
            best_opt = select_best_option(select, label, resume_text, profile_answers)
            if best_opt:
                select.select_option(label=best_opt)
                print(f"  [AUTO-FILL] Dropdown '{label[:35]}' -> Selected '{best_opt}'")
                filled_count += 1
                human_delay((0.8, 1.8))
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
                continue  # already checked
                
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

    # 4. Handle Checkboxes (agreeing to terms, work authorization)
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
    Analyzes the page for validation errors/warnings (missing required fields, red text,
    aria-invalid attributes), resolves missing inputs, and returns the number of fixed issues.
    """
    fixed_count = 0
    try:
        # Find invalid fields
        invalid_fields = page.locator("[aria-invalid='true'], input.error, input.is-invalid, select.error, select.is-invalid, textarea.error").all()
        for field in invalid_fields:
            if not field.is_visible() or field.is_disabled():
                continue
            label = find_label_for_element(page, field)
            tag_name = field.evaluate("el => el.tagName.toLowerCase()")
            
            if tag_name == "select":
                opts = field.locator("option").all()
                if len(opts) > 1:
                    field.select_option(index=1)  # select 1st valid non-empty option
                    print(f"  [FIX-ERROR] Re-selected dropdown option for '{label[:30]}'")
                    fixed_count += 1
            else:
                # Re-fill with answer or default fallback
                ans = answer_question(label, resume_text, profile_answers) or "Yes"
                field.click()
                field.fill(str(ans))
                print(f"  [FIX-ERROR] Re-filled required field '{label[:30]}' -> '{ans}'")
                fixed_count += 1
                
        # Find error message banners / red warning texts
        error_msgs = page.locator(".error-message, .invalid-feedback, .validation-error, .alert-danger, [role='alert']").all()
        for msg in error_msgs:
            if msg.is_visible():
                txt = msg.inner_text().strip()
                if txt:
                    print(f"  [WARNING DETECTED] Page form error: '{txt[:60]}'")
                    # Try triggering form fill pass to ensure no un-filled required field remains
                    extra_fills = fill_form_fields(page, resume_text, profile_answers)
                    if extra_fills > 0:
                        fixed_count += extra_fills
                        
    except Exception:
        pass
    return fixed_count
