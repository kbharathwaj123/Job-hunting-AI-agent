"""
Screening question answering.

Naukri and Indeed apply flows almost always include a set of screening
questions (notice period, CTC, work auth, "describe your experience with
X", yes/no eligibility checks). This module:

  1. Tries to match the question against your fixed `profile_answers`
     (fast, deterministic, no LLM call needed) using fuzzy text matching.
  2. Falls back to the local LLM for anything open-ended, grounding it in
     your resume text + profile facts so it doesn't invent things.
"""

import requests
from rapidfuzz import fuzz

OLLAMA_HOST = "http://localhost:11434"
MODEL = "llama3.1:8b"

# question phrase -> profile_answers key
QUESTION_KEY_MAP = {
    "first name": "first_name",
    "given name": "first_name",
    "last name": "last_name",
    "surname": "last_name",
    "family name": "last_name",
    "full name": "full_name",
    "name": "full_name",
    "total experience": "total_experience_years",
    "years of experience": "total_experience_years",
    "current ctc": "current_ctc",
    "current salary": "current_ctc",
    "expected ctc": "expected_ctc",
    "expected salary": "expected_ctc",
    "notice period": "notice_period",
    "current location": "current_location",
    "willing to relocate": "willing_to_relocate",
    "relocate": "willing_to_relocate",
    "authorized to work": "work_authorization",
    "work authorization": "work_authorization",
    "sponsorship": "work_authorization",
    "highest education": "highest_education",
    "qualification": "highest_education",
    "linkedin profile": "linkedin_url",
    "portfolio": "portfolio_url",
    "phone number": "phone",
    "contact number": "phone",
    "email address": "email",
}

LLM_FALLBACK_PROMPT = """You are filling out a job application screening question truthfully,
based ONLY on the candidate's resume and known facts below. If the resume doesn't
contain enough information to answer confidently, give the most reasonable
short answer implied by the facts provided — do not invent specific
employers, certifications, or achievements not mentioned.

RESUME:
{resume_text}

KNOWN PROFILE FACTS:
{profile_facts}

QUESTION: {question}

Answer in 1-2 sentences max, or a single word/number if the question expects that
(e.g. yes/no, a number, a short phrase). Do not add explanation, just the answer.
"""


def match_fixed_answer(question: str, profile_answers: dict):
    q_lower = question.lower()
    best_key, best_score = None, 0
    for phrase, key in QUESTION_KEY_MAP.items():
        score = fuzz.partial_ratio(phrase, q_lower)
        if score > best_score:
            best_score, best_key = score, key
    if best_score >= 80 and best_key and profile_answers.get(best_key):
        return profile_answers[best_key]
    return None


def llm_answer(question: str, resume_text: str, profile_answers: dict) -> str:
    facts = "\n".join(f"- {k}: {v}" for k, v in profile_answers.items() if v)
    prompt = LLM_FALLBACK_PROMPT.format(
        resume_text=resume_text[:3000],  # keep prompt small/fast
        profile_facts=facts,
        question=question,
    )
    resp = requests.post(
        f"{OLLAMA_HOST}/api/generate",
        json={"model": MODEL, "prompt": prompt, "stream": False},
        timeout=60,
    )
    resp.raise_for_status()
    return resp.json().get("response", "").strip()


def answer_question(question: str, resume_text: str, profile_answers: dict) -> str:
    fixed = match_fixed_answer(question, profile_answers)
    if fixed:
        return fixed
    return llm_answer(question, resume_text, profile_answers)
