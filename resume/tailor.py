"""
Calls a local Ollama model to tailor resume bullets/summary for a specific
job, using the ATS keyword gap so the rewrite is targeted rather than generic.

IMPORTANT: the prompt explicitly instructs the model to only rephrase/
reorder REAL experience — not invent skills or years of experience you
don't have. Fabricated resume content is a bad idea for anyone: it wastes
your time in interviews and can void offers.
"""

import requests
import json

OLLAMA_HOST = "http://localhost:11434"
MODEL = "llama3.1:8b"


TAILOR_PROMPT = """You are helping tailor a real resume for a specific job posting.

RULES (do not break these):
- Only reorder, re-emphasize, or rephrase experience that is ALREADY in the base resume below.
- Do NOT invent skills, tools, employers, titles, or years of experience that aren't present.
- Prioritize bullets and skills that overlap with the job's missing keywords, IF that experience genuinely exists in the base resume.
- Keep it concise and in plain text (no tables, no columns) so it stays ATS-parsable.

BASE RESUME:
{base_resume}

JOB DESCRIPTION:
{job_description}

MISSING KEYWORDS (per ATS scan — only use ones that genuinely apply): {missing_keywords}

Return a tailored professional SUMMARY (3-4 lines) and a reordered list of the
most relevant EXPERIENCE bullets (pulled verbatim or lightly reworded from the
base resume, most relevant first). Output as JSON with keys: "summary", "bullets".
"""


def tailor_resume(base_resume_text: str, job_description: str, missing_keywords: set) -> dict:
    prompt = TAILOR_PROMPT.format(
        base_resume=base_resume_text,
        job_description=job_description,
        missing_keywords=", ".join(list(missing_keywords)[:15]),
    )

    resp = requests.post(
        f"{OLLAMA_HOST}/api/generate",
        json={"model": MODEL, "prompt": prompt, "stream": False, "format": "json"},
        timeout=120,
    )
    resp.raise_for_status()
    raw = resp.json().get("response", "{}")
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        return {"summary": "", "bullets": [], "error": "LLM did not return valid JSON", "raw": raw}
