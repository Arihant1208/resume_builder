from __future__ import annotations

import re
from collections import Counter
from datetime import date

from .models import Certificate, Experience, Profile, Project, Skill

STOPWORDS = {
    "a", "an", "ability", "about", "across", "also", "and", "any", "are",
    "as", "at", "be", "been", "being", "both", "build", "building", "but",
    "by", "can", "candidate", "clients", "client", "colleagues", "come",
    "company", "complex", "contribute", "could", "deliver", "description",
    "do", "each", "effectively", "employer", "end", "engineer",
    "engineering", "ensure", "equal", "etc", "every", "excellent",
    "existing", "experience", "familiarity", "following", "for", "from",
    "full", "get", "growing", "has", "have", "help", "how", "if", "in",
    "including", "into", "is", "it", "its", "job", "just", "knowledge",
    "large", "leverage", "leveraging", "looking", "make", "may", "meet",
    "moderately", "more", "must", "needs", "new", "nice", "not", "one",
    "only", "opportunity", "other", "out", "over", "own", "part",
    "participate", "plus", "posting", "potential", "procedures", "provide",
    "policies", "qualifications", "qualified", "requirements", "required",
    "resolve", "responsibilities", "role", "roles", "scale", "seeking",
    "similar", "skills", "some", "startup", "status", "strong", "such",
    "support", "than", "that", "of", "on", "or", "our", "plus",
    "preferred", "team", "teams", "the", "their", "them", "then",
    "there", "these", "they", "this", "through", "time", "to",
    "understanding", "up", "use", "using", "value", "various", "very",
    "well", "wells", "what", "when", "which", "who", "will", "within",
    "work", "working", "would", "years", "with", "you", "your", "we",
    # Common HR/JD filler words
    "applicants", "application", "apply", "consideration", "demonstrated",
    "disability", "encouraged", "fargo", "hired", "hiring", "training",
    "military", "combination", "equivalent", "education",
    # Generic nouns that cause false matches
    "tools", "tool", "practices", "practice", "services", "service",
    "systems", "system", "based", "level", "high", "used",
    "code", "coding", "develop", "developing", "maintain", "maintaining",
    "design", "challenges", "sound", "making", "drug", "alcohol", "policy",
    # More JD noise words
    "all", "lead", "act", "identify", "risk", "compliance", "regulatory",
    "credit", "market", "financial", "crimes", "operational",
    "governance", "monitoring", "proactive", "remediation", "escalation",
    "decisions", "commensurate", "appetite", "program", "programs",
    "software", "technical", "technologies", "technology", "process",
    "environment", "environments", "initiatives", "deliverables",
    "evaluation", "strategies", "planning", "direction", "guidance",
    "approach", "function", "execution", "focus", "emphasis",
    "disabilities", "accommodation", "recording", "recordings",
    "connection", "recruitment", "recruiting", "represent",
    "mar", "apr", "may", "jun", "date", "posted",
    "stack", "full-time", "about", "ideal",
    # More remaining noise
    "experienced", "expertise", "hands", "prompting", "domain", "test",
    "projects", "issues", "collaborate", "applications", "employment",
    "protected", "applicable", "cross-functional", "cross", "functional",
    "accelerate", "generation", "cleaner", "documentation", "enforce",
    "best", "junior", "senior", "developers", "communication",
    "problem-solving", "collaboration", "end-to-end", "flow", "smooth",
    "components", "integrations", "enterprise", "layers", "optimization",
    "tuning", "above", "deep", "write", "generate", "cases",
    # More noise from JD adjectives/verbs/nouns
    "candidates", "request", "during", "user", "friendly", "rich",
    "responsive", "implement", "integrate", "interfaces", "relational",
    "microsoft", "google", "amazon", "meta", "individual", "information",
    "review", "reviews", "reviewing", "open", "need", "needs",
    # Universal JD noise
    "familiar", "least", "like", "ability", "proven", "ability",
    "passion", "passionate", "eager", "exposure", "proficiency",
}

# ── Step 7: Synonym/alias expansion ──────────────────────────────
# Bidirectional alias groups — any token in a group matches any other.
_ALIAS_GROUPS: list[set[str]] = [
    {"microservices", "microservice", "micro-service"},
    {"restful", "rest"},
    {"ci/cd", "cicd"},
    {"kubernetes", "k8s"},
    {"javascript", "js"},
    {"typescript", "ts"},
    {"postgresql", "postgres"},
    {"object-oriented", "oop", "ooad"},
    {"c#", "csharp", "c-sharp"},
    {".net", "dotnet"},
]

def _build_alias_map() -> dict[str, set[str]]:
    mapping: dict[str, set[str]] = {}
    for group in _ALIAS_GROUPS:
        for term in group:
            mapping[term] = group
    return mapping

ALIASES: dict[str, set[str]] = _build_alias_map()


def _expand_token(token: str) -> set[str]:
    """Return the token itself plus all its aliases."""
    result = {token}
    if token in ALIASES:
        result |= ALIASES[token]
    return result


def _expand_keywords(keywords: set[str]) -> set[str]:
    """Expand a keyword set with all aliases."""
    expanded: set[str] = set()
    for kw in keywords:
        expanded |= _expand_token(kw)
    return expanded


# ── Step 4: Impact / ownership / design signals ──────────────────
_OWNERSHIP_VERBS = {
    "led", "designed", "architected", "built", "owned", "drove",
    "spearheaded", "established", "mentored", "created", "developed",
    "implemented", "engineered", "delivered", "launched", "orchestrated",
}
_DESIGN_SIGNALS = {
    "architecture", "scalable", "microservice", "microservices",
    "distributed", "pipeline", "infrastructure", "high-performance",
    "fault-tolerant", "event-driven",
}
_IMPACT_RE = re.compile(r"\d+\s*%|\d+x|\$\s*\d+", re.IGNORECASE)


def _bonus_score(bullet: str) -> int:
    """Extra points for impact, ownership, and design signals."""
    bonus = 0
    if _IMPACT_RE.search(bullet):
        bonus += 3
    words = bullet.lower().split()
    if words and words[0] in _OWNERSHIP_VERBS:
        bonus += 2
    if any(signal in bullet.lower() for signal in _DESIGN_SIGNALS):
        bonus += 2
    return bonus


# ── Step 5: Seniority detection ──────────────────────────────────
_SENIOR_PATTERNS = re.compile(
    r"\bsenior\b|\bsr\.?\b|\blead\b|\bprincipal\b|\bstaff\b"
    r"|\b[5-9]\+?\s*years?\b|\b\d{2}\+?\s*years?\b"
    r"|\bmentor\b|\barchitect\b",
    re.IGNORECASE,
)
_MID_PATTERNS = re.compile(
    r"\bmid\b|\b[3-4]\+?\s*years?\b",
    re.IGNORECASE,
)

SENIORITY_SENIOR = "SENIOR"
SENIORITY_MID = "MID"
SENIORITY_ENTRY = "ENTRY"


def detect_seniority(job_description: str) -> str:
    if _SENIOR_PATTERNS.search(job_description):
        return SENIORITY_SENIOR
    if _MID_PATTERNS.search(job_description):
        return SENIORITY_MID
    return SENIORITY_ENTRY


# ── Step H: Required vs Desired JD parsing ───────────────────────
_SECTION_HEADERS = re.compile(
    r"(?:^|\n)\s*(required|minimum|must[\- ]have|desired|preferred|nice[\- ]to[\- ]have|bonus)"
    r"\s*(?:qualifications?|skills?|experience|requirements?)?[:\s]*(?:\n|$)",
    re.IGNORECASE,
)

# Markers for sections that should STOP keyword extraction (company blurbs, legal)
_STOP_HEADERS = re.compile(
    r"(?:^|\n)\s*(?:about\s+(?:us|the\s+company|bytedance|team)|"
    r"why\s+join|diversity|benefits|compensation|equal\s+(?:opportunity|employment)|"
    r"job\s+information|disclaimer|eeo\b|accommodation)",
    re.IGNORECASE,
)


def parse_jd_sections(job_description: str) -> dict[str, str]:
    """Split a JD into required / desired / rest sections."""
    # Find where to stop (company blurb / legal sections)
    stop_at = len(job_description)
    stop_match = _STOP_HEADERS.search(job_description)
    if stop_match:
        stop_at = stop_match.start()

    # Only parse within the relevant portion
    relevant = job_description[:stop_at]

    parts: list[tuple[str, int, int]] = []
    for m in _SECTION_HEADERS.finditer(relevant):
        label = m.group(1).lower().strip()
        if label in ("required", "minimum", "must-have", "must have"):
            parts.append(("required", m.start(), m.end()))
        else:
            parts.append(("desired", m.start(), m.end()))

    if not parts:
        return {"required": "", "desired": "", "rest": relevant}

    sections: dict[str, list[str]] = {"required": [], "desired": [], "rest": []}
    # Text before first header is "rest"
    sections["rest"].append(relevant[:parts[0][1]])

    for i, (label, _start, end) in enumerate(parts):
        next_start = parts[i + 1][1] if i + 1 < len(parts) else len(relevant)
        sections[label].append(relevant[end:next_start])

    return {k: "\n".join(v) for k, v in sections.items()}


# ── Tokenization ─────────────────────────────────────────────────
def _tokenize_raw(text: str) -> list[str]:
    """Tokenize without stopword filtering (for bigram detection)."""
    tokens: list[str] = []
    for token in re.findall(r"[a-zA-Z0-9+#/.,-]+", text.lower()):
        cleaned = token.strip(".-,")
        if len(cleaned) < 2:
            continue
        if re.fullmatch(r"\d+\+?", cleaned):
            continue
        tokens.append(cleaned)
    return tokens


def tokenize(text: str) -> list[str]:
    return [t for t in _tokenize_raw(text) if t not in STOPWORDS]


# ── Step 2: Bigram keyword extraction ────────────────────────────
def extract_keywords(job_description: str, limit: int = 40) -> list[str]:
    jd_sections = parse_jd_sections(job_description)

    # Prioritize tokens from the role-relevant parts (desired/required + the job
    # intro) over HR boilerplate that follows after qualifications.
    # Weight desired qualifications heavier by repeating them.
    priority_text = "\n".join([
        jd_sections.get("rest", ""),  # job title, intro, role description
        jd_sections.get("required", ""),
        jd_sections.get("desired", ""),
        jd_sections.get("desired", ""),  # double weight for desired quals
    ]).strip()

    # If no sections were parsed, use the full JD
    source = priority_text or job_description

    tokens = tokenize(source)
    unigram_counts = Counter(tokens)

    # Bigram detection from stopword-filtered tokens — this prevents garbage
    # bigrams like "with disabilities" while keeping "spring boot", "ci/cd pipelines"
    bigram_counts: Counter[str] = Counter()
    for a, b in zip(tokens, tokens[1:]):
        bigram = f"{a} {b}"
        bigram_counts[bigram] += 1

    # Known tech bigrams that should always be recognized
    _TECH_BIGRAMS = {
        "spring boot", "github actions", "docker compose", "github copilot",
        "react native", "object oriented", "design patterns", "sql server",
        "machine learning", "deep learning", "azure functions", "google oauth",
        "rest api", "restful api", "restful apis", "data structures",
        "open source", "real time", "computer science", "ci/cd pipelines",
        "microservices architecture",
    }

    keywords: list[str] = []
    seen: set[str] = set()

    # Add qualifying bigrams: appear 2+ times in the original JD
    # (using filtered tokens to avoid noise), OR match _TECH_BIGRAMS allowlist
    # (using raw tokens so "design patterns" etc. are caught even if a
    # component word is in the unigram stopword list).
    original_filtered = tokenize(job_description)
    original_bigrams: Counter[str] = Counter()
    for a, b in zip(original_filtered, original_filtered[1:]):
        original_bigrams[f"{a} {b}"] += 1

    # Also check raw tokens for tech bigram allowlist matches
    original_raw = _tokenize_raw(job_description)
    raw_bigram_set: set[str] = set()
    for a, b in zip(original_raw, original_raw[1:]):
        raw_bigram_set.add(f"{a} {b}")

    for bigram, count in bigram_counts.most_common():
        if bigram in seen:
            continue
        if original_bigrams.get(bigram, 0) >= 3:
            keywords.append(bigram)
            seen.add(bigram)

    # Add tech bigrams from allowlist found in raw text (even if their
    # component words are stopwords)
    for tech_bg in _TECH_BIGRAMS:
        if tech_bg not in seen and tech_bg in raw_bigram_set:
            keywords.append(tech_bg)
            seen.add(tech_bg)

    # Then unigrams
    for word, _ in unigram_counts.most_common():
        if word not in seen:
            keywords.append(word)
            seen.add(word)

    return keywords[:limit]


# ── Scoring functions ────────────────────────────────────────────
def score_text(text: str, keywords: set[str]) -> int:
    expanded = _expand_keywords(keywords)
    return sum(2 for token in tokenize(text) if _expand_token(token) & expanded)


# Step 1: Tokenize multi-word tags for partial matching
def score_tags(tags: list[str], keywords: set[str]) -> int:
    expanded = _expand_keywords(keywords)
    total = 0
    for tag in tags:
        tag_tokens = set(tokenize(tag))
        # Also check the full tag as-is (lowered)
        tag_tokens.add(tag.lower())
        for tt in tag_tokens:
            if _expand_token(tt) & expanded:
                total += 3
    return total


def score_skill(skill: Skill, keywords: set[str]) -> int:
    return score_text(skill.name, keywords) + score_tags(skill.tags, keywords)


def score_entry(title: str, tags: list[str], bullets: list[str], keywords: set[str]) -> int:
    return (
        score_text(title, keywords)
        + score_tags(tags, keywords)
        + sum(score_text(b, keywords) for b in bullets)
    )


def best_bullets(bullets: list[str], keywords: set[str], limit: int, seniority: str = SENIORITY_ENTRY) -> list[str]:
    ownership_mult = 2 if seniority == SENIORITY_SENIOR else 1

    def _score(bullet: str) -> tuple[int, int, int]:
        kw_score = score_text(bullet, keywords)
        bonus = _bonus_score(bullet)
        # Scale ownership portion by seniority
        words = bullet.lower().split()
        if words and words[0] in _OWNERSHIP_VERBS and seniority == SENIORITY_SENIOR:
            bonus += 2  # extra boost for senior roles
        return (kw_score + bonus * ownership_mult, bonus, len(bullet))

    ranked = sorted(bullets, key=_score, reverse=True)
    return ranked[:limit]


def _profile_terms(profile: Profile) -> set[str]:
    terms: set[str] = set()
    terms.update(tokenize(profile.basics.summary))

    for skill in profile.skills:
        terms.update(tokenize(skill.name))
        for tag in skill.tags:
            terms.update(tokenize(tag))

    for item in profile.experience:
        terms.update(tokenize(item.title))
        terms.update(tokenize(item.company))
        for tag in item.tags:
            terms.update(tokenize(tag))
        for bullet in item.bullets:
            terms.update(tokenize(bullet))

    for item in profile.projects:
        terms.update(tokenize(item.name))
        terms.update(tokenize(item.role))
        for tag in item.tags:
            terms.update(tokenize(tag))
        for bullet in item.bullets:
            terms.update(tokenize(bullet))

    for item in profile.certificates:
        terms.update(tokenize(item.name))
        terms.update(tokenize(item.issuer))
        for tag in item.tags:
            terms.update(tokenize(tag))

    # Expand all profile terms through aliases
    expanded: set[str] = set()
    for t in terms:
        expanded |= _expand_token(t)
    return expanded


# ── Step A: Date sorting helper ──────────────────────────────────
def _parse_end_date(end_date: str) -> date:
    """Parse end_date for sorting. 'Present' → far future, 'YYYY-MM' → date."""
    if not end_date or end_date.lower() == "present":
        return date(9999, 12, 31)
    parts = end_date.split("-")
    year = int(parts[0])
    month = int(parts[1]) if len(parts) > 1 else 1
    return date(year, month, 1)


# ── Step D: Filter tags to tech-relevant terms ───────────────────
_NON_TECH_TAGS = {
    "backend", "frontend", "full-stack", "web", "mobile", "cross-platform",
    "cloud", "deployment", "automation", "api", "spa", "ssr", "database",
    "orm", "cache", "queue", "containers", "orchestration", "devops",
    "observability", "tracing", "monitoring", "payments", "webhooks",
    "authentication", "ai", "llm", "gpt", "embeddings", "product development",
    "portal", "scheduler", "testing", "account management",
    "cloud migration", "cost optimization", "sbom", "supply chain security",
    "nightingalehq", "gosmarter", "ar", "security", "compliance", "audit",
    "threat modeling", "risk scoring", "inventory", "stock tracking",
    "kitchen assistant", "chat application", "pdf", "computer vision",
    "deep learning", "satellite images", "weather api",
    "version control", "developer tools",
    # Company / product names that aren't technologies
    "amazon business",
}


def _tech_tags(tags: list[str], keywords: set[str]) -> list[str]:
    """Filter entry tags to technology names worth rendering."""
    expanded_kw = _expand_keywords(keywords)
    result: list[str] = []
    seen: set[str] = set()
    for tag in tags:
        low = tag.lower()
        if low in _NON_TECH_TAGS:
            continue
        if low in seen:
            continue
        seen.add(low)
        # Prefer tags that match JD keywords, but include all tech tags
        result.append(tag)
    # Sort: JD-matching tags first
    def _relevance(t: str) -> int:
        tokens = set(tokenize(t))
        tokens.add(t.lower())
        return -sum(1 for tt in tokens if _expand_token(tt) & expanded_kw)
    result.sort(key=_relevance)
    return result


# ── Step G: Compute total experience years ───────────────────────
def _total_experience_years(profile: Profile) -> float:
    total_months = 0
    today = date.today()
    for exp in profile.experience:
        start_parts = exp.start_date.split("-") if exp.start_date else []
        if not start_parts:
            continue
        start_year = int(start_parts[0])
        start_month = int(start_parts[1]) if len(start_parts) > 1 else 1
        start = date(start_year, start_month, 1)

        if not exp.end_date or exp.end_date.lower() == "present":
            end = today
        else:
            end_parts = exp.end_date.split("-")
            end_year = int(end_parts[0])
            end_month = int(end_parts[1]) if len(end_parts) > 1 else 12
            end = date(end_year, end_month, 28)

        months = (end.year - start.year) * 12 + (end.month - start.month)
        total_months += max(months, 0)
    return round(total_months / 12, 1)


def _extract_required_years(job_description: str) -> int | None:
    """Extract the minimum years requirement from JD text."""
    m = re.search(r"(\d+)\+?\s*years?", job_description, re.IGNORECASE)
    return int(m.group(1)) if m else None


def _likelihood_label(score: int) -> str:
    if score >= 80:
        return "High"
    if score >= 60:
        return "Moderate"
    if score >= 40:
        return "Medium-Low"
    return "Low"


# ── Step G: Output-level keyword coverage ────────────────────────
def _output_text(tailored: dict) -> str:
    """Flatten a tailored profile dict into plain text for coverage check."""
    parts: list[str] = []
    for cat, skills in tailored.get("skills", {}).items():
        parts.append(cat)
        parts.extend(skills)
    for exp in tailored.get("experience", []):
        parts.append(exp.title)
        parts.append(exp.company)
        parts.extend(exp.bullets)
        parts.extend(tailored.get("tech_tags", {}).get(id(exp), []))
    for proj in tailored.get("projects", []):
        parts.append(proj.name)
        parts.extend(proj.bullets)
        parts.extend(tailored.get("tech_tags", {}).get(id(proj), []))
    if tailored.get("summary"):
        parts.append(tailored["summary"])
    return " ".join(parts)


def analyze_job_fit(profile: Profile, job_description: str) -> dict:
    jd_sections = parse_jd_sections(job_description)
    keywords = extract_keywords(job_description, limit=20)
    keyword_set = set(keywords)
    expanded_kw = _expand_keywords(keyword_set)
    profile_terms = _profile_terms(profile)

    def _keyword_in_profile(kw: str) -> bool:
        """Check if a keyword (unigram or bigram) is covered by profile terms."""
        # Direct match or alias match
        if _expand_token(kw) & profile_terms:
            return True
        # For multi-word keywords, check if ALL component words match
        parts = kw.split()
        if len(parts) > 1:
            return all(_expand_token(p) & profile_terms for p in parts)
        return False

    matched_keywords = [kw for kw in keywords if _keyword_in_profile(kw)]
    missing_keywords = [kw for kw in keywords if not _keyword_in_profile(kw)]
    score = round((len(matched_keywords) / max(len(keywords), 1)) * 100)

    # Flag required-section keyword gaps
    req_keywords = set(extract_keywords(jd_sections["required"], limit=10)) if jd_sections["required"] else set()
    critical_gaps = [kw for kw in req_keywords if not _keyword_in_profile(kw)]

    seniority = detect_seniority(job_description)
    exp_years = _total_experience_years(profile)
    req_years = _extract_required_years(job_description)

    # Penalize likelihood if experience gap is large
    adjusted_score = score
    if req_years and exp_years < req_years * 0.6:
        adjusted_score = max(0, score - 20)
    elif req_years and exp_years < req_years:
        adjusted_score = max(0, score - 10)

    top_skills = sorted(profile.skills, key=lambda s: score_skill(s, keyword_set), reverse=True)
    top_experience = sorted(
        profile.experience,
        key=lambda e: score_entry(f"{e.title} {e.company}", e.tags, e.bullets, keyword_set),
        reverse=True,
    )
    top_projects = sorted(
        profile.projects,
        key=lambda p: score_entry(f"{p.name} {p.role}", p.tags, p.bullets, keyword_set),
        reverse=True,
    )

    strengths: list[str] = []
    for skill in top_skills[:4]:
        if score_skill(skill, keyword_set) > 0:
            strengths.append(f"Skill match: {skill.name}")
    for item in top_experience[:2]:
        if score_entry(f"{item.title} {item.company}", item.tags, item.bullets, keyword_set) > 0:
            strengths.append(f"Relevant experience: {item.title} at {item.company}")
    for item in top_projects[:2]:
        if score_entry(f"{item.name} {item.role}", item.tags, item.bullets, keyword_set) > 0:
            strengths.append(f"Relevant project: {item.name}")

    result: dict = {
        "score": adjusted_score,
        "likelihood": _likelihood_label(adjusted_score),
        "seniority": seniority,
        "matched_keywords": matched_keywords[:10],
        "missing_keywords": missing_keywords[:10],
        "strong_points": strengths[:6],
    }

    if req_years:
        result["experience_years"] = exp_years
        result["required_years"] = req_years
    if critical_gaps:
        result["critical_gaps"] = critical_gaps[:5]

    return result


# ── Step 11: Extract JD title ────────────────────────────────────
def extract_jd_title(job_description: str) -> str:
    """Extract a role title from the first non-empty line of the JD."""
    for line in job_description.splitlines():
        line = line.strip()
        if line and len(line) < 100:
            return line
    return ""


def tailor_profile(profile: Profile, job_description: str) -> dict:
    jd_sections = parse_jd_sections(job_description)
    all_keywords = extract_keywords(job_description)

    # Step H: Required keywords get 2x weight — add them again
    req_keywords = extract_keywords(jd_sections["required"], limit=15) if jd_sections["required"] else []
    weighted: list[str] = all_keywords + req_keywords  # required appear twice
    keywords = set(weighted)

    seniority = detect_seniority(job_description)

    # Step 6: Adaptive limits based on seniority and profile size
    if seniority == SENIORITY_SENIOR:
        exp_bullet_limit = 5
        proj_bullet_limit = 4
    else:
        exp_bullet_limit = 4
        proj_bullet_limit = 3

    max_experience = 3
    max_projects = 3

    # Step 6: If few experiences, include all
    if len(profile.experience) <= max_experience:
        max_experience = len(profile.experience)

    experience = sorted(
        profile.experience,
        key=lambda item: score_entry(f"{item.title} {item.company}", item.tags, item.bullets, keywords),
        reverse=True,
    )[:max_experience]

    # Step A: Re-sort selected experiences by end_date descending (reverse chronological)
    experience.sort(key=lambda item: _parse_end_date(item.end_date), reverse=True)

    projects = sorted(
        profile.projects,
        key=lambda item: score_entry(f"{item.name} {item.role}", item.tags, item.bullets, keywords),
        reverse=True,
    )[:max_projects]

    certificates = sorted(
        profile.certificates,
        key=lambda item: score_entry(f"{item.name} {item.issuer}", item.tags, [], keywords),
        reverse=True,
    )[:4]

    # Step 3: Dynamic skill limits + zero-score filtering
    scored_skills = [(skill, score_skill(skill, keywords)) for skill in profile.skills]
    relevant_skills = [(s, sc) for s, sc in scored_skills if sc > 0]
    relevant_skills.sort(key=lambda x: x[1], reverse=True)

    grouped_skills: dict[str, list[str]] = {}
    count = 0
    for skill, sc in relevant_skills:
        if count >= 16:
            break
        grouped_skills.setdefault(skill.category, []).append(skill.name)
        count += 1

    # Step D: Compute tech tags for each entry
    tech_tags_map: dict[int, list[str]] = {}

    tailored_experience: list[Experience] = []
    for i, item in enumerate(experience):
        bullet_limit = exp_bullet_limit + 1 if i == 0 else exp_bullet_limit
        tailored_experience.append(
            Experience(
                company=item.company,
                title=item.title,
                location=item.location,
                start_date=item.start_date,
                end_date=item.end_date,
                tags=item.tags,
                bullets=best_bullets(item.bullets, keywords, limit=bullet_limit, seniority=seniority),
            )
        )
        tech_tags_map[id(tailored_experience[-1])] = _tech_tags(item.tags, keywords)

    tailored_projects: list[Project] = []
    for i, item in enumerate(projects):
        bullet_limit = proj_bullet_limit + 1 if i == 0 else proj_bullet_limit
        tailored_projects.append(
            Project(
                name=item.name,
                role=item.role,
                link=item.link,
                tags=item.tags,
                bullets=best_bullets(item.bullets, keywords, limit=bullet_limit, seniority=seniority),
            )
        )
        tech_tags_map[id(tailored_projects[-1])] = _tech_tags(item.tags, keywords)

    # Step 11: Extract JD title for header
    jd_title = extract_jd_title(job_description)

    return {
        "keywords": sorted(keywords),
        "skills": grouped_skills,
        "experience": tailored_experience,
        "projects": tailored_projects,
        "certificates": certificates,
        "education": profile.education,
        "achievements": profile.achievements,
        "tech_tags": tech_tags_map,
        "seniority": seniority,
        "jd_title": jd_title,
        "summary": profile.basics.summary,
    }
