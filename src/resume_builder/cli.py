from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path

from .loader import load_job_description, load_profile
from .render_latex import render_resume_latex
from .tailor import tailor_profile

MAPPING_FILE = Path("outputs/mapping.json")


def _load_mapping() -> list[dict]:
    if MAPPING_FILE.exists():
        return json.loads(MAPPING_FILE.read_text(encoding="utf-8"))
    return []


def _save_mapping(entries: list[dict]) -> None:
    MAPPING_FILE.parent.mkdir(parents=True, exist_ok=True)
    MAPPING_FILE.write_text(json.dumps(entries, indent=2) + "\n", encoding="utf-8")


def _auto_output_path(job_path: str) -> Path:
    stem = Path(job_path).stem
    return Path("outputs") / f"resume_{stem}.tex"


def build_resume(profile_path: str, job_path: str, output_path: str | None = None) -> Path:
    profile = load_profile(profile_path)
    job_description = load_job_description(job_path)
    tailored = tailor_profile(profile, job_description)

    content = render_resume_latex(
        basics=profile.basics,
        summary=profile.basics.summary,
        grouped_skills=tailored["skills"],
        experience=tailored["experience"],
        projects=tailored["projects"],
        certificates=tailored["certificates"],
        education=tailored["education"],
        achievements=profile.achievements,
    )

    output = Path(output_path) if output_path else _auto_output_path(job_path)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(content, encoding="utf-8")

    mapping = _load_mapping()
    mapping.append({
        "job": str(Path(job_path)),
        "resume": str(output),
        "generated_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
    })
    _save_mapping(mapping)

    return output


def create_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Generate ATS-friendly tailored resumes.")
    subparsers = parser.add_subparsers(dest="command", required=True)

    build = subparsers.add_parser("build", help="Build a tailored resume from a profile and job description.")
    build.add_argument("--profile", default="data/profile.json", help="Path to profile JSON file (default: data/profile.json).")
    build.add_argument("--job", required=True, help="Path to job description text file.")
    build.add_argument("--output", default=None, help="Output LaTeX file. Auto-generated from job filename if omitted.")

    list_parser = subparsers.add_parser("list", help="List all generated resume mappings.")
    list_parser.add_argument("--json", dest="as_json", action="store_true", help="Output as JSON.")

    return parser


def _list_mappings(as_json: bool) -> int:
    mapping = _load_mapping()
    if not mapping:
        print("No resumes generated yet.")
        return 0
    if as_json:
        print(json.dumps(mapping, indent=2))
    else:
        print(f"{'Job':<40} {'Resume':<40} {'Generated At'}")
        print("-" * 100)
        for entry in mapping:
            print(f"{entry['job']:<40} {entry['resume']:<40} {entry['generated_at']}")
    return 0


def main() -> int:
    parser = create_parser()
    args = parser.parse_args()

    if args.command == "build":
        output_path = build_resume(args.profile, args.job, args.output)
        print(f"Resume written to {output_path}")
        return 0

    if args.command == "list":
        return _list_mappings(args.as_json)

    parser.error("Unknown command")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())