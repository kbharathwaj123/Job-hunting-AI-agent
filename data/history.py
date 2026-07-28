"""
3-Month Rolling Window Applied Jobs History Tracker.

- Keeps track of successfully applied jobs in data/applied_jobs_history.json
- Automatically prunes entries older than 90 days (3 months) on every run.
- Ensures new applications are added to the top.
- Prevents re-applying to the exact same role at the same company within 3 months,
  while allowing different roles at the same company.
"""

import os
import json
import datetime
from pathlib import Path

HISTORY_FILE = Path(__file__).parent.parent / "data" / "applied_jobs_history.json"


def load_history() -> list:
    """Loads history list from JSON file."""
    if HISTORY_FILE.exists():
        try:
            with open(HISTORY_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return []
    return []


def save_history(history: list):
    """Saves history list to JSON file."""
    try:
        HISTORY_FILE.parent.mkdir(parents=True, exist_ok=True)
        with open(HISTORY_FILE, "w", encoding="utf-8") as f:
            json.dump(history, f, indent=2, ensure_ascii=False)
    except Exception as e:
        print(f"[HISTORY WARNING] Could not save history file: {e}")


def prune_old_records(days: int = 90) -> list:
    """
    Deletes entries older than `days` (90 days / 3 months) from the current date.
    Returns the cleaned active history list.
    """
    history = load_history()
    now = datetime.datetime.now()
    cutoff = now - datetime.timedelta(days=days)
    
    cleaned = []
    removed_count = 0
    for entry in history:
        date_str = entry.get("applied_date", "")
        try:
            entry_date = datetime.datetime.fromisoformat(date_str)
            if entry_date >= cutoff:
                cleaned.append(entry)
            else:
                removed_count += 1
        except Exception:
            # If date format invalid, keep or prune based on timestamp fallback
            cleaned.append(entry)
            
    if removed_count > 0:
        print(f"  [HISTORY 🧹] Pruned {removed_count} job application records older than {days} days.")
        save_history(cleaned)
        
    return cleaned


def is_already_applied(company_name: str, role_title: str) -> bool:
    """
    Checks if the exact same role title at the same company was successfully applied
    within the last 3 months. Returns True if already applied, False otherwise.
    Allows different roles at the same company to proceed.
    """
    history = prune_old_records(90)
    c_clean = company_name.strip().lower()
    t_clean = role_title.strip().lower()
    
    for entry in history:
        entry_company = entry.get("company", "").strip().lower()
        entry_title = entry.get("title", "").strip().lower()
        
        # Exact matching for company AND role title
        if entry_company == c_clean and entry_title == t_clean:
            applied_date = entry.get("applied_date_formatted", "recently")
            print(f"  [DEDUP MATCH ⚠️] Already applied to '{role_title}' @ '{company_name}' on {applied_date}.")
            return True
            
    return False


def add_applied_job(job: dict):
    """
    Prepends a newly successfully applied job to the top of the history file.
    """
    history = load_history()
    now = datetime.datetime.now()
    
    record_entry = {
        "company": job.get("company", "").strip(),
        "title": job.get("title", "").strip(),
        "source": job.get("source", "").strip(),
        "url": job.get("url", "").strip(),
        "applied_date": now.isoformat(),
        "applied_date_formatted": now.strftime("%Y-%m-%d %H:%M:%S")
    }
    
    # Avoid duplicate additions in the same list
    history = [h for h in history if not (h.get("company", "").lower() == record_entry["company"].lower() and h.get("title", "").lower() == record_entry["title"].lower())]
    
    # Add new record at the VERY TOP
    history.insert(0, record_entry)
    save_history(history)
    print(f"  [HISTORY 📝] Recorded successful application for '{record_entry['title']}' @ '{record_entry['company']}' at the top of history.")
