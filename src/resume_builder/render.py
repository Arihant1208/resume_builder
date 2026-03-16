from __future__ import annotations

from .models import Basics, Certificate, Education, Experience, Project


def render_header(basics: Basics) -> list[str]:
    contact_parts = [part for part in [basics.location, basics.email, basics.phone, basics.linkedin, basics.github, basics.portfolio] if part]
    lines = [f"# {basics.name}"]
    if basics.title:
        lines.append(basics.title)
    if contact_parts:
        lines.append(" | ".join(contact_parts))
    return lines


def render_summary(summary: str) -> list[str]:
    if not summary:
        return []
    return ["## Summary", summary]


def render_skills(grouped_skills: dict[str, list[str]]) -> list[str]:
    if not grouped_skills:
        return []
    lines = ["## Skills"]
    for category, skills in grouped_skills.items():
        lines.append(f"- {category}: {', '.join(skills)}")
    return lines


def render_experience(experience: list[Experience]) -> list[str]:
    if not experience:
        return []
    lines = ["## Experience"]
    for item in experience:
        date_range = " - ".join(part for part in [item.start_date, item.end_date] if part)
        header_parts = [f"**{item.title}**, {item.company}"]
        trailing = ", ".join(part for part in [item.location, date_range] if part)
        if trailing:
            header_parts.append(trailing)
        lines.append(" | ".join(header_parts))
        for bullet in item.bullets:
            lines.append(f"- {bullet}")
    return lines


def render_projects(projects: list[Project]) -> list[str]:
    if not projects:
        return []
    lines = ["## Projects"]
    for item in projects:
        header = item.name
        if item.role:
            header = f"{header} ({item.role})"
        if item.link:
            header = f"{header} - {item.link}"
        lines.append(header)
        for bullet in item.bullets:
            lines.append(f"- {bullet}")
    return lines


def render_certificates(certificates: list[Certificate]) -> list[str]:
    if not certificates:
        return []
    lines = ["## Certificates"]
    for item in certificates:
        details = ", ".join(part for part in [item.issuer, item.date] if part)
        if details:
            lines.append(f"- {item.name} ({details})")
        else:
            lines.append(f"- {item.name}")
    return lines


def render_education(education: list[Education]) -> list[str]:
    if not education:
        return []
    lines = ["## Education"]
    for item in education:
        date_range = " - ".join(part for part in [item.start_date, item.end_date] if part)
        details = ", ".join(part for part in [item.institution, item.location, date_range] if part)
        lines.append(f"- {item.degree}")
        if details:
            lines.append(f"  {details}")
    return lines


def render_achievements(achievements: list[str]) -> list[str]:
    if not achievements:
        return []
    lines = ["## Achievements"]
    for item in achievements:
        lines.append(f"- {item}")
    return lines


def render_resume(
    basics: Basics,
    summary: str,
    grouped_skills: dict[str, list[str]],
    experience: list[Experience],
    projects: list[Project],
    certificates: list[Certificate],
    education: list[Education],
    achievements: list[str],
) -> str:
    sections = [
        render_header(basics),
        render_summary(summary),
        render_skills(grouped_skills),
        render_experience(experience),
        render_projects(projects),
        render_certificates(certificates),
        render_education(education),
        render_achievements(achievements),
    ]

    lines: list[str] = []
    for section in sections:
        if not section:
            continue
        if lines:
            lines.append("")
        lines.extend(section)
    lines.append("")
    return "\n".join(lines)
