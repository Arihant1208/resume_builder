from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(slots=True)
class Skill:
    name: str
    category: str = "Other"
    tags: list[str] = field(default_factory=list)


@dataclass(slots=True)
class Experience:
    company: str
    title: str
    location: str = ""
    start_date: str = ""
    end_date: str = ""
    tags: list[str] = field(default_factory=list)
    bullets: list[str] = field(default_factory=list)


@dataclass(slots=True)
class Project:
    name: str
    role: str = ""
    link: str = ""
    tags: list[str] = field(default_factory=list)
    bullets: list[str] = field(default_factory=list)


@dataclass(slots=True)
class Certificate:
    name: str
    issuer: str = ""
    date: str = ""
    tags: list[str] = field(default_factory=list)


@dataclass(slots=True)
class Education:
    institution: str
    degree: str
    start_date: str = ""
    end_date: str = ""
    location: str = ""


@dataclass(slots=True)
class Basics:
    name: str
    title: str = ""
    email: str = ""
    phone: str = ""
    location: str = ""
    linkedin: str = ""
    github: str = ""
    portfolio: str = ""
    summary: str = ""


@dataclass(slots=True)
class Profile:
    basics: Basics
    skills: list[Skill] = field(default_factory=list)
    experience: list[Experience] = field(default_factory=list)
    projects: list[Project] = field(default_factory=list)
    certificates: list[Certificate] = field(default_factory=list)
    education: list[Education] = field(default_factory=list)
    achievements: list[str] = field(default_factory=list)
