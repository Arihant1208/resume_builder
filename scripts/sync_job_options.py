from __future__ import annotations

from pathlib import Path


WORKFLOW_PATH = Path(".github/workflows/generate-resume.yml")
JOBS_DIR = Path("jobs")
START_MARKER = "          # job-options:start"
END_MARKER = "          # job-options:end"


def build_options_block() -> list[str]:
    job_files = sorted(path.name for path in JOBS_DIR.glob("*.txt") if path.is_file())
    return [START_MARKER, *[f"          - {name}" for name in job_files], END_MARKER]


def sync_workflow() -> bool:
    lines = WORKFLOW_PATH.read_text(encoding="utf-8").splitlines()

    try:
        start_index = lines.index(START_MARKER)
        end_index = lines.index(END_MARKER)
    except ValueError as exc:
        raise RuntimeError("Workflow markers not found in generate-resume.yml") from exc

    if start_index >= end_index:
        raise RuntimeError("Invalid workflow marker order in generate-resume.yml")

    new_lines = lines[:start_index] + build_options_block() + lines[end_index + 1 :]
    new_content = "\n".join(new_lines) + "\n"
    old_content = "\n".join(lines) + "\n"

    if new_content == old_content:
        return False

    WORKFLOW_PATH.write_text(new_content, encoding="utf-8")
    return True


def main() -> int:
    changed = sync_workflow()
    print("Updated workflow dropdown options." if changed else "Workflow dropdown options already up to date.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
