# Resume Builder

ATS-optimized resume generator that tailors your master profile to any job description. Stores all your experience in structured JSON, scores every entry against the target JD, and produces a focused one-page LaTeX resume designed to pass Applicant Tracking Systems.

## Features

- **Keyword extraction** — parses job descriptions into Required / Desired / rest sections, extracts unigrams and bigrams, filters HR boilerplate with stop-markers.
- **Synonym expansion** — bidirectional alias map (e.g. `kubernetes` ↔ `k8s`, `restful` ↔ `rest`, `ci/cd` ↔ `cicd`) so keyword matching works across variant spellings.
- **Smart scoring** — skills scored by tag + name match; bullets scored by keyword density + ownership verbs + quantified impact + design signals.
- **Seniority detection** — auto-detects SENIOR / MID / ENTRY from JD text and adjusts bullet limits, scoring multipliers, and summary tone.
- **Reverse-chronological ordering** — entries selected by relevance, then re-sorted by end date for ATS compliance.
- **ATS-safe LaTeX** — single-column, no tables, no graphics, PDF metadata (`pdfauthor`, `pdftitle`), correct section names (`Technical Skills`, `Certifications`).
- **Tech stack lines** — renders a `Technologies: ...` italic line under each experience/project entry.
- **Job fit analysis** — computes selection likelihood, flags critical gaps from required qualifications, reports experience vs. requirement.
- **Optional LLM enhancement** — rewrites bullets and generates a tailored summary via Gemini 2.0 Flash (opt-in `--enhance` flag).
- **GitHub Actions CI** — generate resumes and view match analysis directly from the Actions tab.

## Project layout

```
data/
  profile.example.json    # Example profile structure
  profile.json            # Your master profile (git-ignored)
jobs/                     # Job descriptions as plain text
outputs/                  # Generated .tex files + mapping.json
scripts/
  sync_job_options.py     # Syncs job filenames into the GH Actions workflow dropdown
src/resume_builder/
  cli.py                  # CLI entry point (build / analyze / list)
  loader.py               # Loads profile JSON and job description text
  models.py               # Dataclasses: Profile, Skill, Experience, Project, etc.
  tailor.py               # Core engine: keyword extraction, scoring, selection
  render_latex.py         # LaTeX renderer with ATS optimizations
  llm.py                  # Optional Gemini LLM integration
  __main__.py             # python -m resume_builder entry point
.github/workflows/
  generate-resume.yml     # Manual workflow: generate resume + analyze
  sync-job-options.yml    # Auto-sync job dropdown on push to jobs/
```

## Quick start

### Prerequisites

- Python 3.11 or later
- A LaTeX distribution to compile `.tex` → PDF (e.g. [TeX Live](https://tug.org/texlive/), [MiKTeX](https://miktex.org/))

### Installation

```bash
git clone <repo-url>
cd resume
python -m venv .venv
# Windows
.venv\Scripts\activate
# macOS/Linux
source .venv/bin/activate

pip install -e .
```

### Set up your profile

Copy the example and fill in your real data:

```bash
cp data/profile.example.json data/profile.json
```

See [Profile format](#profile-format) below for the full schema.

### Generate a resume

```bash
python -m resume_builder build --job jobs/sample_job.txt
```

Output: `outputs/resume_sample_job.tex`

Override the output path:

```bash
python -m resume_builder build --job jobs/sample_job.txt --output outputs/custom.tex
```

Override the profile path:

```bash
python -m resume_builder build --job jobs/sample_job.txt --profile data/other_profile.json
```

## Commands

### `build` — Generate a tailored resume

```bash
python -m resume_builder build --job <job-file> [--profile <profile>] [--output <path>] [--enhance]
```

| Flag | Default | Description |
|---|---|---|
| `--job` | *(required)* | Path to job description `.txt` file |
| `--profile` | `data/profile.json` | Path to profile JSON |
| `--output` | Auto from job filename | Output `.tex` path |
| `--enhance` | Off | Use Gemini LLM to rewrite bullets and summary |

### `analyze` — Check job fit without building

```bash
python -m resume_builder analyze --job <job-file> [--profile <profile>] [--json]
```

Outputs:
- **Selection likelihood** — percentage score with label (High / Moderate / Medium-Low / Low)
- **Seniority level** — detected from the JD (SENIOR / MID / ENTRY)
- **Experience gap** — your total experience vs. JD requirement
- **Strong points** — top matching skills, experience, and projects
- **Potential gaps** — JD keywords not found in your profile
- **Critical gaps** — keywords from the Required Qualifications section that are missing

Example:

```
Selection likelihood: Low (35%)
Detected seniority level: SENIOR
Your experience: 2.3 years (JD requires 5+)
Strong points:
  + Skill match: Spring Boot
  + Skill match: Java
  + Skill match: CI/CD
Potential gaps:
  - sql server
  - github copilot
CRITICAL gaps (from Required Qualifications):
  ! microservices architecture
```

Use `--json` to get machine-readable output.

### `list` — View all generated resumes

```bash
python -m resume_builder list [--json]
```

Shows the mapping of which resume was generated for which job, with timestamps. Stored in `outputs/mapping.json`. When you rebuild for the same job file, the previous output is automatically replaced.

## Multiple resumes

Save each JD as a separate file in `jobs/`:

```
jobs/google_sde.txt
jobs/amazon_backend.txt
jobs/startup_fullstack.txt
```

Generate each:

```bash
python -m resume_builder build --job jobs/google_sde.txt
python -m resume_builder build --job jobs/amazon_backend.txt
python -m resume_builder build --job jobs/startup_fullstack.txt
```

Produces `outputs/resume_google_sde.tex`, `outputs/resume_amazon_backend.tex`, etc.

## LLM enhancement (optional)

The `--enhance` flag uses Google Gemini 2.0 Flash to:

1. **Rewrite bullets** — weaves JD keywords into your existing bullet points without fabricating facts.
2. **Generate a tailored summary** — produces a 2-3 sentence professional summary matching the role's seniority and top keywords.

### Setup

```bash
pip install -e ".[enhance]"
```

Set your API key:

```bash
# Windows
set GEMINI_API_KEY=your-key-here

# macOS/Linux
export GEMINI_API_KEY=your-key-here
```

Then build with enhancement:

```bash
python -m resume_builder build --job jobs/sample_job.txt --enhance
```

If the API key is missing or the call fails, the builder falls back to your original content silently.

## How the tailoring engine works

The pipeline runs in this order:

### 1. JD parsing

The job description is split into sections:

- **Required** — matched by headers like "Required Qualifications", "Minimum Qualifications", "Must Have"
- **Desired** — matched by "Preferred", "Desired", "Nice to Have", "Bonus"
- **Rest** — everything before the first header (intro, responsibilities)
- **Stopped at** — company blurbs ("About Us", "Why Join", "Diversity", "Benefits") are excluded

### 2. Keyword extraction

From the parsed sections:

- Tokens are extracted with stopword filtering (~170 HR/filler words removed).
- **Bigrams** are detected: known tech bigrams (e.g. `spring boot`, `github actions`, `machine learning`) are always recognized; other bigrams must appear 3+ times in the original JD.
- Unigrams follow, ordered by frequency.
- Required-section keywords get 2× weight in scoring.
- Limit: 40 keywords per JD.

### 3. Scoring

Every profile entry is scored against the keyword set:

| Signal | Points |
|---|---|
| Tag token matches a keyword | +3 per match |
| Bullet text token matches | +2 per match |
| Bullet starts with ownership verb (`led`, `designed`, `architected`, ...) | +2 |
| Bullet contains design signals (`scalable`, `microservices`, `distributed`, ...) | +2 |
| Bullet has quantified impact (`30%`, `3x`, `$50K`) | +3 |
| Senior JD + ownership verb in bullet | ×1.5 multiplier |

Synonyms are expanded bidirectionally during matching:
`microservices` ↔ `microservice`, `kubernetes` ↔ `k8s`, `postgresql` ↔ `postgres`, etc.

### 4. Selection

- **Skills**: Top 16 non-zero-scoring skills, grouped by category.
- **Experience**: Top 3 by score, then re-sorted by end date (most recent first).
- **Projects**: Top 3 by score.
- **Bullets**: Ranked by keyword score + bonus, capped per seniority level (4-5 for experience, 3-4 for projects; first entry gets +1).
- **Certificates**: Top 4 by relevance.
- **Tech tags**: Each entry's tags are filtered to technology names only (company names, generic terms like "backend" are excluded), sorted by JD relevance.

### 5. Rendering

The LaTeX output includes:

- **Header**: Name, JD title (extracted from first JD line), email, LinkedIn, GitHub
- **Summary**: From profile (or LLM-generated with `--enhance`)
- **Technical Skills**: Grouped by category in a bulleted list
- **Experience**: Reverse-chronological, with tech stack lines and ranked bullets
- **Projects**: With tech stack lines, links, and ranked bullets
- **Certifications**: With formatted dates
- **Education**: With GPA and formatted dates
- **Achievements**: Bulleted list

PDF metadata is embedded via `\hypersetup{pdfauthor=..., pdftitle=...}`.

## Profile format

The profile JSON has these top-level sections:

### `basics`

```json
{
  "name": "Your Name",
  "title": "Software Engineer",
  "email": "you@example.com",
  "phone": "",
  "location": "",
  "linkedin": "https://linkedin.com/in/yourprofile",
  "github": "https://github.com/yourusername",
  "portfolio": "",
  "summary": "2-3 sentence professional summary."
}
```

### `skills`

Each skill has a display name, a category (used for grouping in the output), and tags (used for keyword matching):

```json
{
  "name": "Spring Boot",
  "category": "Web Frameworks",
  "tags": ["spring boot", "java", "backend"]
}
```

**Tips**:
- Tags should include lowercase variants, abbreviations, and related terms.
- Categories appear as bold headings in the skills section (e.g. "Languages", "DevOps", "Databases").
- Add more skills than any single resume needs — the engine selects only relevant ones.

### `experience`

```json
{
  "company": "Acme Corp",
  "title": "Software Engineer",
  "location": "San Francisco, CA",
  "start_date": "2022-01",
  "end_date": "Present",
  "tags": ["python", "docker", "kubernetes", "api", "backend"],
  "bullets": [
    "Built a real-time data pipeline processing 10M events/day using Kafka and Python.",
    "Led migration of monolith to 12 microservices, reducing deployment time by 60%."
  ]
}
```

**Tips**:
- Dates use `YYYY-MM` format. Use `"Present"` for current roles.
- Tags should include both technology names and functional descriptors — the engine filters tech names for the "Technologies:" line and uses all tags for scoring.
- Write more bullets than needed (5-8 per role). The engine picks the most relevant ones for each JD.
- Start bullets with strong action verbs. Include metrics where possible.

### `projects`

```json
{
  "name": "AR-Dine",
  "role": "Creator",
  "link": "https://github.com/youruser/ardine",
  "tags": ["react", "docker", "kubernetes", "typescript", "postgresql"],
  "bullets": [
    "Designed an 8-service Docker Compose architecture with PostgreSQL, Redis, and OpenTelemetry.",
    "Implemented Google OAuth, Stripe payments, and real-time order tracking."
  ]
}
```

### `certificates`

```json
{
  "name": "AWS Solutions Architect Associate",
  "issuer": "Amazon Web Services",
  "date": "2024-06",
  "expiry": "2027-06",
  "tags": ["aws", "cloud", "architecture"]
}
```

### `education`

```json
{
  "institution": "University of Technology",
  "degree": "BTech Information Technology",
  "gpa": "8.3",
  "start_date": "2019-08",
  "end_date": "2023-06"
}
```

### `achievements`

A flat list of strings:

```json
[
  "Solved 500+ coding problems across LeetCode, CodeChef, and HackerRank.",
  "Selected for Smart India Hackathon 2022 (External).",
  "3-star programmer on CodeChef."
]
```

## GitHub Actions workflow

Two workflows are included:

### Generate Resume (manual)

1. Push a job file to `jobs/`.
2. Set the `WORKFLOW_SYNC_TOKEN` repository secret with a PAT that has **Contents: Read and write** and **Workflows: Read and write** permissions.
3. The **Sync Job Dropdown Options** workflow runs automatically on push and updates the dropdown choices in the generate workflow.
4. Go to **Actions → Generate Resume → Run workflow**.
5. Select the job filename from the dropdown.
6. The workflow generates the resume, runs the match analysis, and posts results to the run summary.
7. It commits the generated `.tex` file and updated `mapping.json` to `outputs/`.

### Sync Job Options (automatic)

Triggered on every push that modifies `jobs/*.txt`. Updates the `generate-resume.yml` workflow dropdown with current job filenames, using `scripts/sync_job_options.py`.

## Compiling to PDF

The generated `.tex` files use standard LaTeX packages (`geometry`, `enumitem`, `titlesec`, `hyperref`, `fontenc`, `parskip`). Compile with:

```bash
pdflatex outputs/resume_sample_job.tex
```

Or use your IDE's LaTeX build command, Overleaf, or any TeX distribution.

## Data strategy

Keep more detail in your profile than any single resume needs. The generator selects the most relevant content for each target role.

Recommendations:

- Add all real skills, even niche ones — zero-score skills are automatically excluded.
- Write 5-8 bullet points per role/project. The engine picks the best ones.
- Use quantified metrics in bullets (`reduced costs by 30%`, `processed 10M events/day`).
- Start bullets with ownership verbs (`Led`, `Designed`, `Architected`, `Built`).
- Keep tags comprehensive — include full names, abbreviations, and related terms.
- Add functional tags (e.g. `"backend"`, `"authentication"`) alongside technology tags — they help with scoring even though they don't appear in the rendered tech line.
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
