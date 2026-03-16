from __future__ import annotations

import re
from collections import Counter

from .models import Certificate, Experience, Profile, Project, Skill

STOPWORDS = {
    "a",
    "an",
    "ability",
    "and",
    "are",
    "as",
    "at",
    "be",
    "build",
    "building",
    "by",
    "candidate",
    "company",
    "deliver",
    "description",
    "engineer",
    "engineering",
    "excellent",
    "experience",
    "familiarity",
    "for",
    "from",
    "full",
    "growing",
    "have",
    "help",
    "in",
    "is",
    "job",
    "knowledge",
    "looking",
    "nice",
    "plus",
    "requirements",
    "required",
    "responsibilities",
    "role",
    "roles",
    "similar",
    "skills",
    "startup",
    "strong",
    "of",
    "on",
    "or",
    "our",
    "plus",
    "preferred",
    "team",
    "the",
    "their",
    "this",
    "to",
    "understanding",
    "using",
    "years",
    "with",
    "you",
    "your",
    "we",
    "will"
}


def tokenize(text: str) -> list[str]:
    tokens: list[str] = []
    for token in re.findall(r"[a-zA-Z0-9+#.-]+", text.lower()):
        cleaned = token.strip(".-")
        if len(cleaned) < 3:
            continue
        if any(char.isdigit() for char in cleaned):
            continue
        if cleaned in STOPWORDS:
            continue
        tokens.append(cleaned)
    return tokens


def extract_keywords(job_description: str, limit: int = 40) -> list[str]:
    counts = Counter(tokenize(job_description))
    return [word for word, _ in counts.most_common(limit)]


def score_text(text: str, keywords: set[str]) -> int:
    return sum(2 for token in tokenize(text) if token in keywords)


def score_tags(tags: list[str], keywords: set[str]) -> int:
    return sum(3 for tag in tags if tag.lower() in keywords)


def score_skill(skill: Skill, keywords: set[str]) -> int:
    return score_text(skill.name, keywords) + score_tags(skill.tags, keywords)


def score_entry(title: str, tags: list[str], bullets: list[str], keywords: set[str]) -> int:
    return score_text(title, keywords) + score_tags(tags, keywords) + sum(score_text(bullet, keywords) for bullet in bullets)


def best_bullets(bullets: list[str], keywords: set[str], limit: int) -> list[str]:
    ranked = sorted(bullets, key=lambda bullet: (score_text(bullet, keywords), len(bullet)), reverse=True)
    return ranked[:limit]


def _profile_terms(profile: Profile) -> set[str]:
    terms: set[str] = set()
    terms.update(tokenize(profile.basics.summary))

    for skill in profile.skills:
        terms.update(tokenize(skill.name))
        terms.update(tokenize(" ".join(skill.tags)))

    for item in profile.experience:
        terms.update(tokenize(item.title))
        terms.update(tokenize(item.company))
        terms.update(tokenize(" ".join(item.tags)))
        terms.update(tokenize(" ".join(item.bullets)))

    for item in profile.projects:
        terms.update(tokenize(item.name))
        terms.update(tokenize(item.role))
        terms.update(tokenize(" ".join(item.tags)))
        terms.update(tokenize(" ".join(item.bullets)))

    for item in profile.certificates:
        terms.update(tokenize(item.name))
        terms.update(tokenize(item.issuer))
        terms.update(tokenize(" ".join(item.tags)))

    return terms


def _likelihood_label(score: int) -> str:
    if score >= 80:
        return "High"
    if score >= 60:
        return "Moderate"
    if score >= 40:
        return "Medium-Low"
    return "Low"


def analyze_job_fit(profile: Profile, job_description: str) -> dict:
    keywords = extract_keywords(job_description, limit=20)
    keyword_set = set(keywords)
    profile_terms = _profile_terms(profile)

    matched_keywords = [keyword for keyword in keywords if keyword in profile_terms]
    missing_keywords = [keyword for keyword in keywords if keyword not in profile_terms]
    score = round((len(matched_keywords) / max(len(keywords), 1)) * 100)

    top_skills = sorted(profile.skills, key=lambda item: score_skill(item, keyword_set), reverse=True)
    top_experience = sorted(
        profile.experience,
        key=lambda item: score_entry(f"{item.title} {item.company}", item.tags, item.bullets, keyword_set),
        reverse=True,
    )
    top_projects = sorted(
        profile.projects,
        key=lambda item: score_entry(f"{item.name} {item.role}", item.tags, item.bullets, keyword_set),
        reverse=True,
    )

    strengths: list[str] = []
    for skill in top_skills[:4]:
        if score_skill(skill, keyword_set) > 0:
            strengths.append(f"Skill match: {skill.name}")
    for item in top_experience[:2]:
        entry_score = score_entry(f"{item.title} {item.company}", item.tags, item.bullets, keyword_set)
        if entry_score > 0:
            strengths.append(f"Relevant experience: {item.title} at {item.company}")
    for item in top_projects[:2]:
        entry_score = score_entry(f"{item.name} {item.role}", item.tags, item.bullets, keyword_set)
        if entry_score > 0:
            strengths.append(f"Relevant project: {item.name}")

    return {
        "score": score,
        "likelihood": _likelihood_label(score),
        "matched_keywords": matched_keywords[:10],
        "missing_keywords": missing_keywords[:10],
        "strong_points": strengths[:6],
    }


def tailor_profile(profile: Profile, job_description: str) -> dict:
    keywords = set(extract_keywords(job_description))

    experience = sorted(
        profile.experience,
        key=lambda item: score_entry(f"{item.title} {item.company}", item.tags, item.bullets, keywords),
        reverse=True,
    )[:3]
    projects = sorted(
        profile.projects,
        key=lambda item: score_entry(f"{item.name} {item.role}", item.tags, item.bullets, keywords),
        reverse=True,
    )[:3]
    certificates = sorted(
        profile.certificates,
        key=lambda item: score_entry(f"{item.name} {item.issuer}", item.tags, [], keywords),
        reverse=True,
    )[:4]
    skills = sorted(profile.skills, key=lambda item: score_skill(item, keywords), reverse=True)

    grouped_skills: dict[str, list[str]] = {}
    for skill in skills[:12]:
        grouped_skills.setdefault(skill.category, []).append(skill.name)

    tailored_experience: list[Experience] = []
    for item in experience:
        tailored_experience.append(
            Experience(
                company=item.company,
                title=item.title,
                location=item.location,
                start_date=item.start_date,
                end_date=item.end_date,
                tags=item.tags,
                bullets=best_bullets(item.bullets, keywords, limit=4),
            )
        )

    tailored_projects: list[Project] = []
    for item in projects:
        tailored_projects.append(
            Project(
                name=item.name,
                role=item.role,
                link=item.link,
                tags=item.tags,
                bullets=best_bullets(item.bullets, keywords, limit=3),
            )
        )

    return {
        "keywords": sorted(keywords),
        "skills": grouped_skills,
        "experience": tailored_experience,
        "projects": tailored_projects,
        "certificates": certificates,
        "education": profile.education,
    }
