from __future__ import annotations

import json
from pathlib import Path

from .models import Basics, Certificate, Education, Experience, Profile, Project, Skill


def load_profile(profile_path: str | Path) -> Profile:
    path = Path(profile_path)
    data = json.loads(path.read_text(encoding="utf-8"))

    basics = Basics(**data["basics"])
    skills = [Skill(**item) for item in data.get("skills", [])]
    experience = [Experience(**item) for item in data.get("experience", [])]
    projects = [Project(**item) for item in data.get("projects", [])]
    certificates = [Certificate(**item) for item in data.get("certificates", [])]
    education = [Education(**item) for item in data.get("education", [])]

    return Profile(
        basics=basics,
        skills=skills,
        experience=experience,
        projects=projects,
        certificates=certificates,
        education=education,
        achievements=data.get("achievements", []),
    )


def load_job_description(job_path: str | Path) -> str:
    return Path(job_path).read_text(encoding="utf-8")
