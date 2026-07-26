"""
Company verification module.

Checks if a company is legitimate before applying, using:
  1. Basic name checks (red flags like "hiring agency 123", too-short names)
  2. Google search to verify the company exists and has a real web presence
  3. Flags suspicious patterns (no website, very new, bad reviews keywords)

Returns a verdict: "legit", "suspicious", or "unknown"
"""

import requests
import re

# Red-flag patterns in company names
SUSPICIOUS_NAME_PATTERNS = [
    r"(?i)(confidential|undisclosed|hiring\s*agency|stealth|dummy)",
    r"(?i)(work\s*from\s*home\s*job|earn\s*money|data\s*entry\s*job)",
    r"(?i)(freelanc|part.?time.*earn|whatsapp)",
]

# Keywords that suggest fake/scam postings
SCAM_KEYWORDS = [
    "registration fee", "pay to apply", "advance payment", "security deposit",
    "guaranteed income", "earn from home", "no experience needed work from home",
    "mlm", "network marketing", "forex trading job",
]

# Well-known companies (skip verification for these)
KNOWN_COMPANIES = {
    "google", "microsoft", "amazon", "apple", "meta", "facebook", "netflix",
    "tcs", "infosys", "wipro", "hcl", "cognizant", "accenture", "capgemini",
    "deloitte", "kpmg", "ey", "pwc", "ibm", "oracle", "sap", "salesforce",
    "adobe", "vmware", "cisco", "intel", "samsung", "flipkart", "paytm",
    "swiggy", "zomato", "ola", "uber", "phonepe", "razorpay", "byju",
    "freshworks", "zoho", "thoughtworks", "atlassian", "qualcomm", "nvidia",
    "bureau veritas", "myntra", "meesho", "cred", "dream11", "nykaa",
    "jpmorgan", "goldman sachs", "morgan stanley", "barclays", "hsbc",
    "deutsche bank", "societe generale", "ubs", "credit suisse",
    "cgi", "nice", "luxoft", "hexaware", "mphasis", "ltimindtree", "persistent",
    "zensar", "cyient", "coforge", "birlasoft", "larsen", "tech mahindra",
    "dxc", "ntt", "atos", "sopra", "valtech", "epam", "globant",
    "teksystems", "robert half", "randstad", "manpower", "adecco",
    "msci", "proofpoint", "drivetrain",
}


def is_name_suspicious(company_name: str) -> bool:
    """Check if the company name itself has red flags."""
    for pattern in SUSPICIOUS_NAME_PATTERNS:
        if re.search(pattern, company_name):
            return True
    return False


def is_known_company(company_name: str) -> bool:
    """Check if it's a well-known company (skip further checks)."""
    name_lower = company_name.lower().strip()
    for known in KNOWN_COMPANIES:
        if known in name_lower or name_lower in known:
            return True
    return False


def check_job_description_scam(job_description: str) -> bool:
    """Check if the job description contains scam keywords."""
    desc_lower = job_description.lower()
    return any(kw in desc_lower for kw in SCAM_KEYWORDS)


def verify_company_online(company_name: str, ollama_host: str = "http://localhost:11434",
                           model: str = "llama3.1:8b") -> dict:
    """
    Uses the local LLM to assess if a company name sounds legitimate
    based on its training knowledge. This is a lightweight check — not
    a substitute for manual research, but catches obvious fakes.
    """
    prompt = f"""Is "{company_name}" a real, legitimate company that hires software engineers/testers?
Answer with ONLY one of these three words: LEGIT, SUSPICIOUS, or UNKNOWN.
Then on the next line, give a one-sentence reason."""

    try:
        resp = requests.post(
            f"{ollama_host}/api/generate",
            json={"model": model, "prompt": prompt, "stream": False},
            timeout=30,
        )
        resp.raise_for_status()
        answer = resp.json().get("response", "").strip()
        first_line = answer.split("\n")[0].strip().upper()

        if "LEGIT" in first_line:
            return {"verdict": "legit", "reason": answer}
        elif "SUSPICIOUS" in first_line:
            return {"verdict": "suspicious", "reason": answer}
        else:
            return {"verdict": "unknown", "reason": answer}
    except Exception:
        return {"verdict": "unknown", "reason": "Could not verify (LLM unavailable)"}


import urllib.parse

def get_company_rating_and_reviews(page, company_name: str) -> dict:
    """
    Search Google with the persistent browser profile to extract rating and review counts.
    Returns: {'rating': float, 'reviews': int}
    """
    query = f"{company_name} reviews rating"
    url = f"https://www.google.com/search?q={urllib.parse.quote(query)}"
    
    try:
        page.goto(url, timeout=15000)
        page.wait_for_timeout(2000)
    except Exception as e:
        return {'rating': None, 'reviews': 0}
        
    text = page.locator('body').inner_text()
    lines = [line.strip() for line in text.split('\n') if line.strip()]
    
    # 1. Rating matches (e.g. 3.7/5)
    ratings_5 = [float(r) for r in re.findall(r'(\d\.\d)\s*/\s*5', text)]
    
    # 2. Rated X.X or Rating X.X
    ratings_rated = [float(r) for r in re.findall(r'(?:Rating|Rated)\s*(\d\.\d)', text, re.IGNORECASE)]
    
    # 3. Rating and review count patterns: e.g. 3.7(60) or 4.1(2.5k)
    ratings_paren = []
    matches_paren = re.findall(r'(\d\.\d)\s*\(\s*([\d\.\,kKmM]+)\s*\)', text)
    for r_str, c_str in matches_paren:
        c_str = c_str.upper().replace(',', '')
        count = 0
        if 'K' in c_str:
            count = int(float(c_str.replace('K', '').strip()) * 1000)
        elif 'M' in c_str:
            count = int(float(c_str.replace('M', '').strip()) * 1000000)
        else:
            try:
                count = int(c_str)
            except ValueError:
                pass
        ratings_paren.append((float(r_str), count))
        
    # 4. Based on Y reviews
    counts = []
    matches_count = re.findall(r'based\s+on\s+(?:over\s+)?([\d\.\,kKmM]+)\s+reviews', text, re.IGNORECASE)
    for c_str in matches_count:
        c_str = c_str.upper().replace(',', '')
        count = 0
        if 'K' in c_str:
            count = int(float(c_str.replace('K', '').strip()) * 1000)
        elif 'M' in c_str:
            count = int(float(c_str.replace('M', '').strip()) * 1000000)
        else:
            try:
                count = int(c_str)
            except ValueError:
                pass
        counts.append(count)
        
    # Aggregate
    max_reviews = 0
    best_rating = None
    
    for r, count in ratings_paren:
        if count > max_reviews:
            max_reviews = count
            best_rating = r
            
    if counts:
        potential_count = max(counts)
        if potential_count > max_reviews:
            max_reviews = potential_count
            if ratings_5:
                best_rating = ratings_5[0]
            elif ratings_rated:
                best_rating = ratings_rated[0]
                
    if best_rating is None:
        if ratings_5:
            best_rating = ratings_5[0]
        elif ratings_rated:
            best_rating = ratings_rated[0]
            
    return {'rating': best_rating, 'reviews': max_reviews}


def verify_company(company_name: str, page=None, job_description: str = "",
                    min_rating: float = 3.5, min_reviews: int = 150,
                    ollama_host: str = "http://localhost:11434",
                    model: str = "llama3.1:8b") -> dict:
    """
    Main verification function. Returns:
      {"verdict": "legit"|"suspicious"|"skip_low_rating"|"unknown", "reason": "...", "rating": float, "reviews": int}
    """
    company_name = company_name.strip()
    result = {"verdict": "unknown", "reason": "Unchecked", "rating": None, "reviews": 0}

    # Quick checks first
    if not company_name:
        result.update({"verdict": "suspicious", "reason": "No company name provided"})
        return result

    if is_name_suspicious(company_name):
        result.update({"verdict": "suspicious", "reason": f"Company name '{company_name}' has red-flag patterns"})
        return result

    if job_description and check_job_description_scam(job_description):
        result.update({"verdict": "suspicious", "reason": "Job description contains scam-like keywords"})
        return result

    # Check online ratings if page is available
    if page:
        ratings_info = get_company_rating_and_reviews(page, company_name)
        rating = ratings_info['rating']
        reviews = ratings_info['reviews']
        result.update({"rating": rating, "reviews": reviews})
        
        # If it is a known company, we can accept it if no reviews found or if it matches
        is_known = is_known_company(company_name)
        
        if rating is not None:
            if rating < min_rating or reviews < min_reviews:
                # If it's a known company, let's still verify rating, but maybe be slightly lenient.
                # However, user's instruction is strict: rating >= 3.5 and reviews >= 150.
                reason = f"Rating: {rating}/5 (min {min_rating}), Reviews: {reviews} (min {min_reviews})"
                result.update({"verdict": "skip_low_rating", "reason": reason})
                return result
            else:
                reason = f"Rating: {rating}/5, Reviews: {reviews}"
                result.update({"verdict": "legit", "reason": reason})
                return result
        else:
            if is_known:
                result.update({"verdict": "legit", "reason": f"Known company '{company_name}' (No rating found)"})
                return result
            else:
                result.update({"verdict": "skip_low_rating", "reason": f"No ratings or reviews found on Google search"})
                return result

    if is_known_company(company_name):
        result.update({"verdict": "legit", "reason": f"'{company_name}' is a well-known company"})
        return result

    # For unknown companies, ask the LLM as fallback
    llm_res = verify_company_online(company_name, ollama_host, model)
    result.update({"verdict": llm_res["verdict"], "reason": llm_res["reason"]})
    return result
