from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path

from .loader import load_job_description, load_profile
from .render_latex import render_resume_latex
from .tailor import analyze_job_fit, tailor_profile

MAPPING_FILE = Path("outputs/mapping.json")


def _normalize_path(value: str | Path) -> str:
    return Path(value).as_posix()


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


def _remove_existing_resume_outputs(mapping: list[dict], job_path: str, output: Path) -> list[dict]:
    normalized_job = _normalize_path(job_path)
    kept_entries: list[dict] = []

    for entry in mapping:
        entry_job = _normalize_path(entry["job"])
        if entry_job != normalized_job:
            kept_entries.append(entry)
            continue

        existing_resume = Path(entry["resume"])
        if existing_resume != output and existing_resume.exists():
            existing_resume.unlink()

    return kept_entries


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
    )

    output = Path(output_path) if output_path else _auto_output_path(job_path)
    output.parent.mkdir(parents=True, exist_ok=True)

    mapping = _load_mapping()
    mapping = _remove_existing_resume_outputs(mapping, job_path, output)

    output.write_text(content, encoding="utf-8")

    mapping.append({
        "job": _normalize_path(job_path),
        "resume": _normalize_path(output),
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

    analyze = subparsers.add_parser("analyze", help="Analyze how well your profile matches a job description.")
    analyze.add_argument("--profile", default="data/profile.json", help="Path to profile JSON file (default: data/profile.json).")
    analyze.add_argument("--job", required=True, help="Path to job description text file.")
    analyze.add_argument("--json", dest="as_json", action="store_true", help="Output analysis as JSON.")

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


def _analyze(profile_path: str, job_path: str, as_json: bool) -> int:
    profile = load_profile(profile_path)
    job_description = load_job_description(job_path)
    analysis = analyze_job_fit(profile, job_description)

    if as_json:
        print(json.dumps(analysis, indent=2))
        return 0

    print(f"Selection likelihood: {analysis['likelihood']} ({analysis['score']}%)")
    print("Strong points:")
    for item in analysis["strong_points"]:
        print(f"- {item}")
    print("Potential gaps:")
    for item in analysis["missing_keywords"]:
        print(f"- {item}")
    return 0


def main() -> int:
    parser = create_parser()
    args = parser.parse_args()

    if args.command == "build":
        output_path = build_resume(args.profile, args.job, args.output)
        print(f"Resume written to {output_path}")
        return 0

    if args.command == "analyze":
        return _analyze(args.profile, args.job, args.as_json)

    if args.command == "list":
        return _list_mappings(args.as_json)

    parser.error("Unknown command")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())