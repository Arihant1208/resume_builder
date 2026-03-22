from __future__ import annotations

import re

from .models import Basics, Certificate, Education, Experience, Project

# Characters that need escaping in LaTeX text
_LATEX_SPECIAL = re.compile(r"([#$%&_{}~^\\])")

# ── Step B: Month name lookup ────────────────────────────────────
_MONTHS = {
    "01": "Jan", "02": "Feb", "03": "Mar", "04": "Apr",
    "05": "May", "06": "Jun", "07": "Jul", "08": "Aug",
    "09": "Sep", "10": "Oct", "11": "Nov", "12": "Dec",
}


def _format_date(iso: str) -> str:
    """Convert '2023-01' → 'Jan 2023', 'Present' stays as-is."""
    if not iso or iso.lower() == "present":
        return iso or ""
    parts = iso.split("-")
    if len(parts) == 2 and parts[1] in _MONTHS:
        return f"{_MONTHS[parts[1]]} {parts[0]}"
    return iso


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

def _make_preamble(basics: Basics, title: str) -> str:
    """Generate preamble with PDF metadata (Step F)."""
    author = _escape(basics.name)
    pdf_title = _escape(f"{basics.name} - {title}" if title else basics.name)
    return rf"""\documentclass[11pt,a4paper]{{article}}

% ── Packages ──
\usepackage[margin=0.6in]{{geometry}}
\usepackage{{enumitem}}
\usepackage{{titlesec}}
\usepackage[hidelinks, pdfauthor={{{author}}}, pdftitle={{{pdf_title}}}]{{hyperref}}
\usepackage{{fontenc}}
\usepackage{{parskip}}

% ── Section formatting ──
\titleformat{{\section}}{{\large\bfseries\uppercase}}{{}}{{0pt}}{{}}[\titlerule]
\titlespacing*{{\section}}{{0pt}}{{8pt}}{{4pt}}

% ── List formatting ──
\setlist[itemize]{{nosep, left=0pt, labelsep=4pt, itemsep=1pt}}

% ── No page numbers ──
\pagestyle{{empty}}

\begin{{document}}
"""

POSTAMBLE = r"""
\end{document}
"""


# ── Section renderers ─────────────────────────────────────────────

def render_header(basics: Basics, title_override: str = "") -> str:
    lines: list[str] = []
    lines.append(r"\begin{center}")
    lines.append(rf"{{\LARGE \textbf{{{_escape(basics.name)}}}}}")
    title = title_override or basics.title
    if title:
        lines.append(rf"\\ {_escape(title)}")

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


# Step C: ATS-standard section name
def render_skills(grouped_skills: dict[str, list[str]]) -> str:
    if not grouped_skills:
        return ""
    lines = [r"\section{Technical Skills}", r"\begin{itemize}"]
    for category, skills in grouped_skills.items():
        joined = ", ".join(_escape(s) for s in skills)
        lines.append(rf"  \item \textbf{{{_escape(category)}}}: {joined}")
    lines.append(r"\end{itemize}")
    return "\n".join(lines)


# Step D: Tech stack line helper
def _render_tech_line(tags: list[str]) -> str:
    """Render an italic Technologies: line from a list of tag strings."""
    if not tags:
        return ""
    # Title-case the tags for display
    display = [t.title() if t.islower() else t for t in tags]
    joined = ", ".join(_escape(d) for d in display)
    return rf"\\ \textit{{Technologies: {joined}}}"


def render_experience(experience: list[Experience], tech_tags: dict[int, list[str]] | None = None) -> str:
    if not experience:
        return ""
    tech_tags = tech_tags or {}
    lines = [r"\section{Experience}"]
    for item in experience:
        # Step B: Format dates
        date_range = " -- ".join(_format_date(p) for p in [item.start_date, item.end_date] if p)
        lines.append(
            rf"\textbf{{{_escape(item.title)}}}, {_escape(item.company)} \hfill {_escape(date_range)}"
        )
        if item.location:
            lines.append(rf"\\ \textit{{{_escape(item.location)}}}")
        # Step D: Tech stack line
        entry_tags = tech_tags.get(id(item), [])
        tech_line = _render_tech_line(entry_tags)
        if tech_line:
            lines.append(tech_line)
        lines.append(r"\begin{itemize}")
        for bullet in item.bullets:
            lines.append(rf"  \item {_escape(bullet)}")
        lines.append(r"\end{itemize}")
        lines.append(r"\vspace{2pt}")
    return "\n".join(lines)


def render_projects(projects: list[Project], tech_tags: dict[int, list[str]] | None = None) -> str:
    if not projects:
        return ""
    tech_tags = tech_tags or {}
    lines = [r"\section{Projects}"]
    for item in projects:
        header = rf"\textbf{{{_escape(item.name)}}}"
        if item.role:
            header += rf" ({_escape(item.role)})"
        if item.link:
            header += rf" -- {_href(item.link)}"
        lines.append(header)
        # Step D: Tech stack line
        entry_tags = tech_tags.get(id(item), [])
        tech_line = _render_tech_line(entry_tags)
        if tech_line:
            lines.append(tech_line)
        lines.append(r"\begin{itemize}")
        for bullet in item.bullets:
            lines.append(rf"  \item {_escape(bullet)}")
        lines.append(r"\end{itemize}")
        lines.append(r"\vspace{2pt}")
    return "\n".join(lines)


# Step C: ATS-standard section name
def render_certificates(certificates: list[Certificate]) -> str:
    if not certificates:
        return ""
    lines = [r"\section{Certifications}", r"\begin{itemize}"]
    for item in certificates:
        details = ", ".join(_format_date(p) if "-" in p else p for p in [item.issuer, item.date] if p)
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
        # Step B: Format dates
        date_range = " -- ".join(_format_date(p) for p in [item.start_date, item.end_date] if p)
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


# Step E: Render achievements section
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
    achievements: list[str] | None = None,
    tech_tags: dict[int, list[str]] | None = None,
    title_override: str = "",
) -> str:
    preamble = _make_preamble(basics, title_override or basics.title)

    sections = [
        render_header(basics, title_override),
        render_summary(summary),
        render_skills(grouped_skills),
        render_experience(experience, tech_tags),
        render_projects(projects, tech_tags),
        render_certificates(certificates),
        render_education(education),
        render_achievements(achievements or []),
    ]

    body = "\n\n".join(s for s in sections if s)
    return preamble + body + POSTAMBLE
