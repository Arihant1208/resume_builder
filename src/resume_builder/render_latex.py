from __future__ import annotations

import re

from .models import Basics, Certificate, Education, Experience, Project

# Characters that need escaping in LaTeX text
_LATEX_SPECIAL = re.compile(r"([#$%&_{}~^\\])")


def _escape(text: str) -> str:
    """Escape LaTeX special characters in plain text."""
    replacements = {
        "\\": r"\textbackslash{}",
        "~": r"\textasciitilde{}",
        "^": r"\textasciicircum{}",
        "#": r"\#",
        "$": r"\$",
        "%": r"\%",
        "&": r"\&",
        "_": r"\_",
        "{": r"\{",
        "}": r"\}",
    }
    out: list[str] = []
    for ch in text:
        out.append(replacements.get(ch, ch))
    return "".join(out)


def _href(url: str, display: str | None = None) -> str:
    return rf"\href{{{url}}}{{{_escape(display or url)}}}"


# ── Document skeleton ──────────────────────────────────────────────

PREAMBLE = r"""\documentclass[11pt,a4paper]{article}

% ── Packages ──
\usepackage[margin=0.6in]{geometry}
\usepackage{enumitem}
\usepackage{titlesec}
\usepackage[hidelinks]{hyperref}
\usepackage{fontenc}
\usepackage{parskip}

% ── Section formatting ──
\titleformat{\section}{\large\bfseries\uppercase}{}{0pt}{}[\titlerule]
\titlespacing*{\section}{0pt}{8pt}{4pt}

% ── List formatting ──
\setlist[itemize]{nosep, left=0pt, labelsep=4pt, itemsep=1pt}

% ── No page numbers ──
\pagestyle{empty}

\begin{document}
"""

POSTAMBLE = r"""
\end{document}
"""


# ── Section renderers ─────────────────────────────────────────────

def render_header(basics: Basics) -> str:
    lines: list[str] = []
    lines.append(r"\begin{center}")
    lines.append(rf"{{\LARGE \textbf{{{_escape(basics.name)}}}}}")
    if basics.title:
        lines.append(rf"\\ {_escape(basics.title)}")

    contact: list[str] = []
    if basics.location:
        contact.append(_escape(basics.location))
    if basics.email:
        contact.append(_href(f"mailto:{basics.email}", basics.email))
    if basics.phone:
        contact.append(_escape(basics.phone))
    if basics.linkedin:
        contact.append(_href(basics.linkedin, "LinkedIn"))
    if basics.github:
        contact.append(_href(basics.github, "GitHub"))
    if basics.portfolio:
        contact.append(_href(basics.portfolio, "Portfolio"))

    if contact:
        lines.append(r"\\ " + r" $\mid$ ".join(contact))

    lines.append(r"\end{center}")
    return "\n".join(lines)


def render_summary(summary: str) -> str:
    if not summary:
        return ""
    return f"\\section{{Summary}}\n{_escape(summary)}"


def render_skills(grouped_skills: dict[str, list[str]]) -> str:
    if not grouped_skills:
        return ""
    lines = [r"\section{Skills}", r"\begin{itemize}"]
    for category, skills in grouped_skills.items():
        joined = ", ".join(_escape(s) for s in skills)
        lines.append(rf"  \item \textbf{{{_escape(category)}}}: {joined}")
    lines.append(r"\end{itemize}")
    return "\n".join(lines)


def render_experience(experience: list[Experience]) -> str:
    if not experience:
        return ""
    lines = [r"\section{Experience}"]
    for item in experience:
        date_range = " -- ".join(part for part in [item.start_date, item.end_date] if part)
        lines.append(
            rf"\textbf{{{_escape(item.title)}}}, {_escape(item.company)} \hfill {_escape(date_range)}"
        )
        if item.location:
            lines.append(rf"\\ \textit{{{_escape(item.location)}}}")
        lines.append(r"\begin{itemize}")
        for bullet in item.bullets:
            lines.append(rf"  \item {_escape(bullet)}")
        lines.append(r"\end{itemize}")
        lines.append(r"\vspace{2pt}")
    return "\n".join(lines)


def render_projects(projects: list[Project]) -> str:
    if not projects:
        return ""
    lines = [r"\section{Projects}"]
    for item in projects:
        header = rf"\textbf{{{_escape(item.name)}}}"
        if item.role:
            header += rf" ({_escape(item.role)})"
        if item.link:
            header += rf" -- {_href(item.link)}"
        lines.append(header)
        lines.append(r"\begin{itemize}")
        for bullet in item.bullets:
            lines.append(rf"  \item {_escape(bullet)}")
        lines.append(r"\end{itemize}")
        lines.append(r"\vspace{2pt}")
    return "\n".join(lines)


def render_certificates(certificates: list[Certificate]) -> str:
    if not certificates:
        return ""
    lines = [r"\section{Certificates}", r"\begin{itemize}"]
    for item in certificates:
        details = ", ".join(part for part in [item.issuer, item.date] if part)
        entry = _escape(item.name)
        if details:
            entry += rf" ({_escape(details)})"
        lines.append(rf"  \item {entry}")
    lines.append(r"\end{itemize}")
    return "\n".join(lines)


def render_education(education: list[Education]) -> str:
    if not education:
        return ""
    lines = [r"\section{Education}"]
    for item in education:
        date_range = " -- ".join(part for part in [item.start_date, item.end_date] if part)
        lines.append(
            rf"\textbf{{{_escape(item.degree)}}} \hfill {_escape(date_range)}"
        )
        details: list[str] = []
        if item.institution:
            details.append(item.institution)
        if item.location:
            details.append(item.location)
        if details:
            lines.append(rf"\\ {_escape(', '.join(details))}")
        lines.append(r"\vspace{2pt}")
    return "\n".join(lines)


def render_achievements(achievements: list[str]) -> str:
    if not achievements:
        return ""
    lines = [r"\section{Achievements}", r"\begin{itemize}"]
    for item in achievements:
        lines.append(rf"  \item {_escape(item)}")
    lines.append(r"\end{itemize}")
    return "\n".join(lines)


# ── Main entry point ──────────────────────────────────────────────

def render_resume_latex(
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

    body = "\n\n".join(s for s in sections if s)
    return PREAMBLE + body + POSTAMBLE
