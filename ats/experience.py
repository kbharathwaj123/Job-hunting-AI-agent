"""
Experience parser & eligibility filter module.
Extracts required experience ranges from job descriptions / titles and evaluates candidate eligibility.
"""

import re


def extract_experience_requirement(text: str) -> tuple[int | None, int | None]:
    """
    Parses required experience range (min_years, max_years) from job description or title.
    Returns (min_years, max_years). Values may be None if not explicitly stated.
    """
    if not text:
        return None, None

    text_lower = text.lower()

    # Pattern 1: Range like "2-5 years", "3 to 6 Yrs", "0 - 2 yrs", "2 – 5 years"
    range_match = re.search(r'(\d+)\s*(?:-|to|–)\s*(\d+)\s*(?:yrs|years|yr|year)', text_lower)
    if range_match:
        min_y = int(range_match.group(1))
        max_y = int(range_match.group(2))
        return min_y, max_y

    # Pattern 2: "5+ years", "10+ yrs", "8+ years"
    plus_match = re.search(r'(\d+)\s*\+\s*(?:yrs|years|yr|year)', text_lower)
    if plus_match:
        min_y = int(plus_match.group(1))
        return min_y, None

    # Pattern 3: "8 years+", "10 yrs+"
    plus_match_2 = re.search(r'(\d+)\s*(?:yrs|years|yr|year)\s*\+', text_lower)
    if plus_match_2:
        min_y = int(plus_match_2.group(1))
        return min_y, None

    # Pattern 4: "minimum 5 years", "at least 4 yrs", "min 3 years"
    min_match = re.search(r'(?:minimum|at least|min\.?)\s*(\d+)\s*(?:yrs|years|yr|year)', text_lower)
    if min_match:
        min_y = int(min_match.group(1))
        return min_y, None

    # Pattern 5: "5 years of experience", "3 yrs experience"
    exp_match = re.search(r'(\d+)\s*(?:yrs|years|yr|year)\s*(?:of\s*)?(?:relevant\s*)?exp', text_lower)
    if exp_match:
        val = int(exp_match.group(1))
        return val, val

    return None, None


def is_experience_eligible(
    candidate_exp: float | int,
    min_allowed: int,
    max_allowed: int,
    job_description: str,
    job_title: str = ""
) -> tuple[bool, str]:
    """
    Determines if a job's experience requirement is suitable for the candidate.

    Example:
      Candidate exp = 3 years, allowed range = 2 to 5 years.
      - Job requires 2-5 yrs -> Eligible
      - Job requires 3-6 yrs -> Eligible
      - Job requires 8-12 yrs -> Not eligible
      - Job requires 10+ yrs -> Not eligible
    """
    full_text = f"{job_title} {job_description}"
    min_req, max_req = extract_experience_requirement(full_text)

    # If no experience requirement was found in text, treat as eligible
    if min_req is None and max_req is None:
        return True, "No specific experience requirement detected in posting"

    # Case 1: Range provided (e.g. min_req = 8, max_req = 12)
    if min_req is not None and max_req is not None:
        if min_req > max_allowed or min_req > (candidate_exp + 2):
            return False, f"Job requires {min_req}-{max_req} yrs exp (Candidate exp: {candidate_exp} yrs, allowed max: {max_allowed} yrs)"
        return True, f"Job requirement {min_req}-{max_req} yrs matches candidate exp ({candidate_exp} yrs)"

    # Case 2: Minimum experience only (e.g. 5+ years, 10+ years, min 8 years)
    if min_req is not None:
        if min_req > max_allowed or min_req > (candidate_exp + 2):
            return False, f"Job requires {min_req}+ yrs exp (Candidate exp: {candidate_exp} yrs, allowed max: {max_allowed} yrs)"
        return True, f"Job requirement {min_req}+ yrs matches candidate exp ({candidate_exp} yrs)"

    return True, "Experience check passed"
