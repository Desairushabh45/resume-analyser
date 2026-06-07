"""
suggestions.py – Generate actionable improvement suggestions for a resume.

Aggregates insights from the ATS checker, skill gap analysis, and general
best-practice rules to produce a prioritised list of recommendations.
"""

from ats_checker import run_ats_check
from skills_extractor import extract_skills, categorise_skills
from job_matcher import skill_gap_analysis


def _priority_label(priority: int) -> str:
    """Map numeric priority (1-3) to a human label."""
    return {1: "🔴 High", 2: "🟡 Medium", 3: "🟢 Low"}.get(priority, "ℹ️ Info")


def _make_suggestion(category: str, priority: int, message: str) -> dict:
    """Create a structured suggestion dict."""
    return {
        "category": category,
        "priority": priority,
        "label": _priority_label(priority),
        "message": message,
    }


def generate_suggestions(
    parsed: dict,
    job_description: str | None = None,
) -> list[dict]:
    """
    Return a prioritised list of improvement suggestions.

    Each suggestion dict contains:
        category  – "ATS", "Skills", "Content", "Formatting"
        priority  – 1 (high), 2 (medium), 3 (low)
        label     – human-readable priority tag with emoji
        message   – the actionable suggestion text

    Parameters
    ----------
    parsed : dict
        Output of ``parser.parse_resume()``.
    job_description : str | None
        If provided, includes skill-gap and keyword-density suggestions.
    """
    suggestions: list[dict] = []
    text = parsed.get("text", "")

    # ── 1. ATS-based suggestions ─────────────────────────────────────────
    ats_report = run_ats_check(parsed)
    for check in ats_report["checks"]:
        for issue in check["issues"]:
            priority = 1 if check["score"] < 60 else (2 if check["score"] < 80 else 3)
            suggestions.append(_make_suggestion("ATS", priority, issue))

    # ── 2. Skill-gap suggestions (when a JD is provided) ─────────────────
    if job_description:
        gap = skill_gap_analysis(text, job_description)

        missing = gap.get("missing", [])
        if len(missing) > 5:
            suggestions.append(_make_suggestion(
                "Skills", 1,
                f"Your resume is missing {len(missing)} skills from the job "
                f"description: {', '.join(missing[:10])}{'…' if len(missing) > 10 else ''}. "
                f"Add the ones you possess, or consider upskilling.",
            ))
        elif missing:
            suggestions.append(_make_suggestion(
                "Skills", 2,
                f"Missing skills: {', '.join(missing)}. Add them if applicable.",
            ))

        matching = gap.get("matching", [])
        if matching:
            suggestions.append(_make_suggestion(
                "Skills", 3,
                f"You already list these relevant skills: "
                f"{', '.join(matching)}. Ensure they're prominently featured "
                f"and backed by concrete experience.",
            ))

        extra = gap.get("extra", [])
        if len(extra) > 10:
            suggestions.append(_make_suggestion(
                "Skills", 3,
                f"You list {len(extra)} skills not required by this job. "
                f"Consider removing less-relevant ones to keep your resume focused.",
            ))

    # ── 3. General content suggestions ───────────────────────────────────
    sections = parsed.get("sections", {})

    if "summary" not in sections and "objective" not in sections \
            and "professional summary" not in sections:
        suggestions.append(_make_suggestion(
            "Content", 2,
            "Add a professional Summary or Objective section at the top "
            "to immediately grab the reader's attention.",
        ))

    skills = extract_skills(text)
    categories = categorise_skills(skills)

    if "Soft Skills" not in categories:
        suggestions.append(_make_suggestion(
            "Content", 3,
            "Consider mentioning soft skills like leadership, communication, "
            "or teamwork to present a well-rounded profile.",
        ))

    if len(skills) < 5:
        suggestions.append(_make_suggestion(
            "Content", 2,
            "Only a few skills were detected. Expand your Skills section "
            "with specific tools, languages, and frameworks you know.",
        ))
    elif len(skills) > 30:
        suggestions.append(_make_suggestion(
            "Content", 3,
            f"{len(skills)} skills detected – that's a lot! Consider "
            "curating to highlight only the most relevant ones.",
        ))

    # Education check
    education = parsed.get("education", [])
    if not education and "education" not in sections:
        suggestions.append(_make_suggestion(
            "Content", 2,
            "No education details detected. Add your degree(s) and "
            "institution(s) even if you're experienced.",
        ))

    # Experience years
    years = parsed.get("years_of_experience")
    if years and years > 0:
        word_count = parsed.get("word_count", 0)
        if years >= 10 and word_count < 400:
            suggestions.append(_make_suggestion(
                "Content", 2,
                f"You mention {years}+ years of experience but your resume "
                f"is only {word_count} words. Add more detail about your "
                f"key accomplishments.",
            ))

    # Sort by priority (highest first)
    suggestions.sort(key=lambda s: s["priority"])
    return suggestions


def format_suggestions_text(suggestions: list[dict]) -> str:
    """Return a plain-text formatted summary of suggestions."""
    if not suggestions:
        return "✅ No suggestions – your resume looks great!"

    lines: list[str] = []
    for i, s in enumerate(suggestions, 1):
        lines.append(f"{i}. [{s['label']}] ({s['category']}) {s['message']}")
    return "\n".join(lines)


def get_suggestion_stats(suggestions: list[dict]) -> dict:
    """Return a summary of suggestion priorities and categories."""
    high = sum(1 for s in suggestions if s["priority"] == 1)
    medium = sum(1 for s in suggestions if s["priority"] == 2)
    low = sum(1 for s in suggestions if s["priority"] == 3)

    cats: dict[str, int] = {}
    for s in suggestions:
        cats[s["category"]] = cats.get(s["category"], 0) + 1

    return {
        "total": len(suggestions),
        "high": high,
        "medium": medium,
        "low": low,
        "by_category": cats,
    }
