from __future__ import annotations

import re
from collections import Counter

from .models import Certificate, Experience, Profile, Project, Skill

STOPWORDS = {
    "a",
    "an",
    "and",
    "are",
    "as",
    "at",
    "be",
    "build",
    "by",
    "for",
    "from",
    "in",
    "is",
    "of",
    "on",
    "or",
    "the",
    "to",
    "with",
    "you",
    "your",
    "we",
    "will"
}


def tokenize(text: str) -> list[str]:
    return [token for token in re.findall(r"[a-zA-Z0-9+#.-]+", text.lower()) if token not in STOPWORDS]


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
