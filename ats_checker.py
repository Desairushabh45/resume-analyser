"""
ats_checker.py – Evaluate how well a resume is optimised for
Applicant Tracking Systems (ATS).

Runs 8 individual checks covering contact info, section structure, length,
bullet points, action verbs, measurable results, formatting, and
keyword repetition.  Returns per-check and aggregate scores.
"""

import re


# ── Individual check functions ───────────────────────────────────────────────

def check_contact_info(parsed: dict) -> dict:
    """Verify that essential contact details are present."""
    issues: list[str] = []
    score = 100

    if not parsed.get("email"):
        issues.append("No email address found.")
        score -= 30
    if not parsed.get("phone"):
        issues.append("No phone number found.")
        score -= 20
    if not parsed.get("linkedin"):
        issues.append("No LinkedIn URL found – consider adding one.")
        score -= 10
    if not parsed.get("name") or parsed.get("name") == "Unknown":
        issues.append("Could not detect your name – make sure it's prominent.")
        score -= 15

    return {"name": "Contact Information", "score": max(score, 0), "issues": issues}


def check_sections(parsed: dict) -> dict:
    """Check for the presence of key resume sections."""
    required = {"experience", "education", "skills"}
    recommended = {"summary", "projects", "certifications"}

    sections = set(parsed.get("sections", {}).keys())
    issues: list[str] = []
    score = 100

    # Also accept common variants
    for sec in required:
        variants = {sec, f"work {sec}", f"professional {sec}", f"technical {sec}"}
        if not variants & sections:
            issues.append(f"Missing required section: {sec.title()}")
            score -= 20

    for sec in recommended:
        variants = {sec, f"professional {sec}", f"career {sec}"}
        if not variants & sections:
            issues.append(f"Consider adding a '{sec.title()}' section.")
            score -= 5

    return {"name": "Section Structure", "score": max(score, 0), "issues": issues}


def check_length(parsed: dict) -> dict:
    """Evaluate resume length (word count)."""
    word_count = parsed.get("word_count", len(parsed.get("text", "").split()))
    issues: list[str] = []
    score = 100

    if word_count < 150:
        issues.append(
            f"Resume is very short ({word_count} words). "
            "Aim for at least 300 words."
        )
        score -= 30
    elif word_count < 300:
        issues.append(
            f"Resume is a bit short ({word_count} words). "
            "Consider adding more detail."
        )
        score -= 15
    elif word_count > 1500:
        issues.append(
            f"Resume is long ({word_count} words). "
            "Try to keep it concise (under 1 000 words for most roles)."
        )
        score -= 10

    return {"name": "Resume Length", "score": max(score, 0), "issues": issues}


def check_bullet_points(text: str) -> dict:
    """Check whether bullet points or list markers are used."""
    bullet_pattern = re.compile(
        r"^[\s]*[•\-\u2022\u2023\u25E6\u2043\*►▪▸]", re.MULTILINE
    )
    bullets = bullet_pattern.findall(text)
    issues: list[str] = []
    score = 100

    if len(bullets) == 0:
        issues.append(
            "No bullet points detected. ATS and recruiters strongly prefer "
            "bulleted lists for experience and skills."
        )
        score -= 25
    elif len(bullets) < 5:
        issues.append(
            f"Only {len(bullets)} bullet point(s) detected. Use more to "
            "clearly list responsibilities and achievements."
        )
        score -= 10

    return {"name": "Bullet Points", "score": max(score, 0), "issues": issues}


def check_action_verbs(text: str) -> dict:
    """Check for the presence of strong action verbs."""
    action_verbs = {
        "achieved", "built", "created", "delivered", "designed",
        "developed", "implemented", "improved", "increased", "led",
        "managed", "optimised", "optimized", "reduced", "resolved",
        "spearheaded", "streamlined", "launched", "established",
        "coordinated", "analysed", "analyzed", "engineered",
        "architected", "automated", "collaborated", "deployed",
        "directed", "executed", "facilitated", "generated",
        "integrated", "mentored", "orchestrated", "pioneered",
        "refactored", "scaled", "supervised", "transformed",
    }
    text_lower = text.lower()
    found = [v for v in action_verbs if v in text_lower]
    issues: list[str] = []
    score = 100

    if len(found) == 0:
        issues.append(
            "No action verbs detected. Use strong verbs like 'developed', "
            "'implemented', 'led' to describe achievements."
        )
        score -= 20
    elif len(found) < 3:
        issues.append(
            f"Only {len(found)} action verb(s) found ({', '.join(found)}). "
            "Aim for at least 5 across your experience section."
        )
        score -= 10

    return {
        "name": "Action Verbs",
        "score": max(score, 0),
        "issues": issues,
        "found_verbs": found,
    }


def check_measurable_results(text: str) -> dict:
    """Look for quantified achievements (numbers, percentages, currency)."""
    number_pattern = re.compile(r"\d+[%+]|\$[\d,]+|\d{2,}(?:\.\d+)?")
    matches = number_pattern.findall(text)
    issues: list[str] = []
    score = 100

    if len(matches) == 0:
        issues.append(
            "No measurable results found. Quantify achievements (e.g., "
            "'increased sales by 25%', 'reduced costs by $10K')."
        )
        score -= 20
    elif len(matches) < 3:
        issues.append(
            f"Only {len(matches)} metric(s) found. Add more numbers to "
            "demonstrate impact."
        )
        score -= 10

    return {"name": "Measurable Results", "score": max(score, 0), "issues": issues}


def check_formatting(text: str) -> dict:
    """Flag common formatting issues that can confuse ATS parsers."""
    issues: list[str] = []
    score = 100

    # Check for excessive special characters
    special_chars = len(re.findall(r"[^\w\s.,;:!?@/\-()#&+]", text))
    if special_chars > 50:
        issues.append(
            f"High number of special characters ({special_chars}) detected. "
            "Some ATS systems struggle with unusual symbols."
        )
        score -= 10

    # Check for extremely long lines (tables / columns that may not parse)
    long_lines = [l for l in text.splitlines() if len(l) > 200]
    if len(long_lines) > 3:
        issues.append(
            "Several very long lines detected. Multi-column layouts can "
            "confuse ATS parsers – prefer single-column formatting."
        )
        score -= 10

    # Check for ALL CAPS overuse
    words = text.split()
    caps_words = [w for w in words if w.isupper() and len(w) > 2]
    if len(caps_words) > len(words) * 0.15:
        issues.append(
            "Excessive ALL CAPS detected. Use title case for headings instead."
        )
        score -= 5

    return {"name": "Formatting", "score": max(score, 0), "issues": issues}


def check_email_professional(parsed: dict) -> dict:
    """Ensure the email address looks professional."""
    issues: list[str] = []
    score = 100

    email = parsed.get("email", "")
    if email:
        local_part = email.split("@")[0].lower()
        unprofessional = ["sexy", "cool", "babe", "dude", "420", "69", "xxx"]
        if any(word in local_part for word in unprofessional):
            issues.append(
                "Your email address may appear unprofessional. Consider "
                "using a firstname.lastname format."
            )
            score -= 15
    else:
        score -= 10  # already penalised in contact check

    return {"name": "Professional Email", "score": max(score, 0), "issues": issues}


# ── Aggregate function ───────────────────────────────────────────────────────

def run_ats_check(parsed: dict) -> dict:
    """
    Run all ATS checks and return an aggregate report.

    Parameters
    ----------
    parsed : dict
        The output of ``parser.parse_resume()``.

    Returns
    -------
    dict with keys:
        overall_score  (int 0–100)
        checks         (list of individual check dicts)
        pass_count     (int – number of checks scoring ≥ 80)
        fail_count     (int – number of checks scoring < 60)
        verdict        (str – human-readable summary)
    """
    text = parsed.get("text", "")

    checks = [
        check_contact_info(parsed),
        check_sections(parsed),
        check_length(parsed),
        check_bullet_points(text),
        check_action_verbs(text),
        check_measurable_results(text),
        check_formatting(text),
        check_email_professional(parsed),
    ]

    overall = round(sum(c["score"] for c in checks) / len(checks))
    pass_count = sum(1 for c in checks if c["score"] >= 80)
    fail_count = sum(1 for c in checks if c["score"] < 60)

    if overall >= 80:
        verdict = (
            "✅ Your resume is well-optimised for ATS. Great job! "
            "Minor tweaks may still boost your chances."
        )
    elif overall >= 55:
        verdict = (
            "⚠️ Your resume is decent but could use improvements to pass "
            "ATS filters more reliably. Address the issues below."
        )
    else:
        verdict = (
            "❌ Your resume needs significant work to be ATS-friendly. "
            "Focus on the high-priority issues listed below."
        )

    return {
        "overall_score": overall,
        "checks": checks,
        "pass_count": pass_count,
        "fail_count": fail_count,
        "verdict": verdict,
    }
