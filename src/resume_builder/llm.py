"""Optional LLM integration for bullet rewriting and summary generation.

Requires: GEMINI_API_KEY environment variable and google-generativeai package.
Falls back gracefully if either is missing.
"""
from __future__ import annotations

import os

from .models import Basics

_MODEL_NAME = "gemini-2.0-flash"


def _get_client():
    """Return a configured Gemini GenerativeModel, or None."""
    api_key = os.environ.get("GEMINI_API_KEY", "")
    if not api_key:
        return None
    try:
        from google import generativeai as genai
        genai.configure(api_key=api_key)
        return genai.GenerativeModel(_MODEL_NAME)
    except Exception:
        return None


def _ask(model, prompt: str) -> str:
    """Send a prompt and return stripped text, or empty string on failure."""
    try:
        response = model.generate_content(prompt)
        return response.text.strip()
    except Exception:
        return ""


def rewrite_bullets(
    bullets: list[str],
    jd_keywords: list[str],
    seniority: str,
    role_title: str,
) -> list[str]:
    """Rewrite resume bullets to weave in missing JD keywords where factual."""
    model = _get_client()
    if model is None:
        return bullets

    kw_str = ", ".join(jd_keywords[:15])
    rewritten: list[str] = []

    for bullet in bullets:
        prompt = (
            f"You are a resume bullet rewriter. The candidate is applying for: "
            f"{role_title} ({seniority} level).\n\n"
            f"Rewrite this resume bullet point:\n\"{bullet}\"\n\n"
            f"Rules:\n"
            f"1. These JD keywords should be woven in ONLY if they accurately "
            f"describe the work: {kw_str}\n"
            f"2. Preserve ALL factual content. Do NOT invent metrics or responsibilities.\n"
            f"3. Start with a strong action verb.\n"
            f"4. Keep quantified impact if present in original.\n"
            f"5. One sentence, max 35 words.\n"
            f"6. Return ONLY the rewritten bullet, no quotes, no explanation.\n"
        )
        result = _ask(model, prompt)
        rewritten.append(result if result else bullet)

    return rewritten


def generate_summary(
    basics: Basics,
    top_skills: list[str],
    jd_keywords: list[str],
    seniority: str,
    role_title: str,
) -> str:
    """Generate a 2-3 sentence professional summary tailored to the JD."""
    model = _get_client()
    if model is None:
        return basics.summary

    skills_str = ", ".join(top_skills[:10])
    kw_str = ", ".join(jd_keywords[:10])

    prompt = (
        f"Write a 2-3 sentence professional summary for a resume.\n"
        f"Role: {role_title} ({seniority} level)\n"
        f"Candidate's top matching skills: {skills_str}\n"
        f"Key JD keywords to include naturally: {kw_str}\n"
        f"Candidate's current title: {basics.title}\n\n"
        f"Rules:\n"
        f"1. Must naturally include at least 5 of the JD keywords.\n"
        f"2. ATS-friendly: no jargon, no fluff, factual.\n"
        f"3. Match seniority tone — senior = leadership + architecture, "
        f"entry = execution + growth.\n"
        f"4. Do NOT mention years of experience or specific company names.\n"
        f"5. Return ONLY the summary text, no quotes.\n"
    )

    result = _ask(model, prompt)
    return result if result else basics.summary
