# Resume Builder

This repository keeps your full professional profile in one place and generates tailored, ATS-friendly resumes from a job description.

## What this repo does

- Stores your master profile in structured JSON.
- Ranks experience, projects, skills, and certificates against a job description.
- Produces a focused resume in LaTeX that is easy to compile to PDF.
- Keeps the generated output clean and ATS-safe by avoiding tables, columns, and visual-only formatting.

## Project layout

- `data/profile.example.json`: Example master profile structure.
- `jobs/`: Put job descriptions here as plain text files.
- `outputs/`: Generated resumes are written here.
- `src/resume_builder/`: Resume generation code.

## Quick start

1. Install Python 3.11+.
2. Create a virtual environment if you want one.
3. Install the project in editable mode:

```bash
python -m pip install -e .
```

4. Copy `data/profile.example.json` to `data/profile.json` and replace the sample data with your real information.
5. Save a target job description as a text file inside `jobs/`.
6. Run:

```bash
python -m resume_builder build --job jobs/sample_job.txt
```

The output file is auto-named from the job file: `outputs/resume_sample_job.tex`. You can override it:

```bash
python -m resume_builder build --job jobs/sample_job.txt --output outputs/custom_name.tex
```

Profile defaults to `data/profile.json`. Override with `--profile`.

## Multiple resumes

Save each job description as a separate file in `jobs/`:

```
jobs/google_sde.txt
jobs/amazon_backend.txt
jobs/startup_fullstack.txt
```

Generate a resume for each:

```bash
python -m resume_builder build --job jobs/google_sde.txt
python -m resume_builder build --job jobs/amazon_backend.txt
python -m resume_builder build --job jobs/startup_fullstack.txt
```

This produces `outputs/resume_google_sde.tex`, `outputs/resume_amazon_backend.tex`, etc.

## Mapping: which resume was built for which job

Every build appends to `outputs/mapping.json`. View it as a table:

If a resume already exists for the same job file, the old mapped output is removed and the mapping entry is replaced with the latest generated file.

```bash
python -m resume_builder list
```

Or as raw JSON:

```bash
python -m resume_builder list --json
```

## GitHub Actions workflow

A manual workflow lets you generate a resume from GitHub without a local setup.

1. Push a job file to `jobs/`.
2. The `Sync Job Dropdown Options` workflow automatically updates the dropdown choices after the push.
3. Go to **Actions → Generate Resume → Run workflow**.
4. Select the job filename from the dropdown.
5. The workflow generates the resume, analyzes your fit for the role, and shows selection likelihood, strong points, and gaps in the run summary.
6. It then commits the generated resume and updated mapping to `outputs/`.

## Data strategy

Keep more detail than any single resume needs. The generator will choose the most relevant content and order it for the target role.

Recommended approach:

- Add all real skills, even if they are not on every resume.
- Add multiple bullet points per role and project.
- Add tags to each item so matching is better.
- Keep bullet points outcome-focused and factual.

## ATS guidance

- Use exact terms that appear in the job description when they truthfully match your background.
- Keep section headings conventional: `Summary`, `Skills`, `Experience`, `Projects`, `Certificates`, `Education`.
- Avoid keyword stuffing. Relevance and accuracy matter more than repetition.
- Export to PDF only after checking spacing and readability.

## Next improvements

- Add multiple resume templates.
- Generate a cover letter draft.
- Score match percentage by section.
- Export directly to DOCX or PDF.
