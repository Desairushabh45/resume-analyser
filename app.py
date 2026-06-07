"""
app.py – Streamlit web application for the AI Resume Analyzer.

Launch with:
    python -m streamlit run app.py

Design:
    - Clean white background with purple (#534AB7) accent
    - SVG circular progress ring for ATS score
    - Pill-style skill badges
    - Modern SaaS-style dashboard
"""

import tempfile
from pathlib import Path

import streamlit as st

from parser import parse_resume
from skills_extractor import extract_skills, categorise_skills, extract_skills_with_frequency
from ats_checker import run_ats_check
from job_matcher import match_resume_to_job
from suggestions import generate_suggestions, get_suggestion_stats

# ── Page config ──────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="AI Resume Analyzer",
    page_icon="📄",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ── Constants ────────────────────────────────────────────────────────────────
PRIMARY = "#6C63FF"
PRIMARY_LIGHT = "#8F89FF"
PRIMARY_BG = "#F3F2FF"
TEXT_DARK = "#1E293B"
TEXT_MED = "#64748B"
TEXT_LIGHT = "#94A3B8"
SUCCESS = "#10B981"
WARNING = "#F59E0B"
DANGER = "#EF4444"
CARD_BG = "#FFFFFF"
PAGE_BG = "#FAFAFE"

# ── Global CSS ───────────────────────────────────────────────────────────────
st.markdown(f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');

/* Reset Streamlit defaults */
html, body, [class*="css"] {{
    font-family: 'Inter', -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
}}
.stApp {{
    background: {PAGE_BG};
}}
header[data-testid="stHeader"] {{
    background: transparent;
}}
.block-container {{
    padding-top: 2rem;
    max-width: 1100px !important;
    margin: 0 auto;
}}

/* Hide Streamlit branding */
#MainMenu, footer {{ visibility: hidden; }}

/* ── Hero Section ────────────────────────────────────── */
.hero-badge {{
    display: inline-block;
    background: {PRIMARY_BG};
    color: {PRIMARY};
    padding: 6px 14px;
    border-radius: 20px;
    font-size: 0.78rem;
    font-weight: 600;
    margin-bottom: 12px;
}}
.hero-title {{
    font-size: 2.5rem;
    font-weight: 800;
    color: {TEXT_DARK};
    line-height: 1.2;
    margin-top: 10px;
    margin-bottom: 12px;
}}
.hero-sub {{
    font-size: 1rem;
    color: {TEXT_MED};
    margin-bottom: 24px;
    line-height: 1.6;
}}

/* ── Cards ────────────────────────────────────────────── */
.card {{
    background: {CARD_BG};
    border: 1px solid #F1F5F9;
    border-radius: 12px;
    padding: 24px;
    height: 100%;
    box-shadow: 0 4px 20px rgba(0, 0, 0, 0.03);
    transition: box-shadow 0.25s ease, transform 0.25s ease;
}}
.card:hover {{
    box-shadow: 0 8px 30px rgba(108, 99, 255, 0.05);
    transform: translateY(-1px);
}}
.card-title {{
    font-size: 0.8rem;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: 1.2px;
    color: {TEXT_MED};
    margin-bottom: 20px;
}}
.card-value {{
    font-size: 2rem;
    font-weight: 800;
    color: {TEXT_DARK};
}}
.card-sub {{
    font-size: 0.85rem;
    color: {TEXT_MED};
    margin-top: 4px;
}}

/* ── Progress Ring ────────────────────────────────────── */
.ring-container {{
    display: flex;
    flex-direction: column;
    align-items: center;
    padding: 10px 0;
}}
.ring-label {{
    font-size: 0.82rem;
    color: {TEXT_LIGHT};
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 1px;
    margin-top: 12px;
}}

/* ── Progress Bars ────────────────────────────────────── */
.progress-item {{
    margin-bottom: 18px;
}}
.progress-header {{
    display: flex;
    justify-content: space-between;
    margin-bottom: 6px;
}}
.progress-name {{
    font-size: 0.85rem;
    font-weight: 600;
    color: {TEXT_DARK};
}}
.progress-pct {{
    font-size: 0.85rem;
    font-weight: 700;
    color: {PRIMARY};
}}
.progress-track {{
    height: 10px;
    background: {PRIMARY_BG};
    border-radius: 5px;
    overflow: hidden;
}}
.progress-fill {{
    height: 100%;
    border-radius: 5px;
    background: linear-gradient(90deg, {PRIMARY}, {PRIMARY_LIGHT});
    transition: width 0.8s ease;
}}

/* ── Skill Pills ──────────────────────────────────────── */
.skill-pill {{
    display: inline-block;
    padding: 6px 14px;
    margin: 4px;
    border-radius: 20px;
    font-size: 0.8rem;
    font-weight: 600;
    background: {PRIMARY_BG};
    color: {PRIMARY};
    border: 1px solid #EBE9FE;
    transition: all 0.2s ease;
}}
.skill-pill:hover {{
    background: {PRIMARY};
    color: #fff;
    transform: translateY(-1px);
}}
.skill-pill.detected {{
    background: #F3F0FF;
    color: #5B21B6;
}}

/* ── Missing Keyword Row ──────────────────────────────── */
.kw-row {{
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 12px 0;
    border-bottom: 1px solid #F1F5F9;
}}
.kw-row:last-child {{ border-bottom: none; }}
.kw-info {{
    display: flex;
    align-items: center;
    gap: 12px;
}}
.kw-name {{
    font-size: 0.9rem;
    font-weight: 600;
    color: {TEXT_DARK};
}}
.kw-priority {{
    font-size: 0.72rem;
    font-weight: 700;
    padding: 3px 8px;
    border-radius: 12px;
    text-transform: uppercase;
    letter-spacing: 0.5px;
}}
.kw-priority.high {{
    background: #FEE2E2;
    color: {DANGER};
}}
.kw-priority.medium {{
    background: #FFEDD5;
    color: {WARNING};
}}
.kw-priority.low {{
    background: #F1F5F9;
    color: {TEXT_MED};
}}
.kw-add-btn {{
    display: inline-block;
    padding: 5px 12px;
    border-radius: 6px;
    font-size: 0.78rem;
    font-weight: 600;
    background: #F3F2FF;
    color: {PRIMARY};
    text-decoration: none;
    cursor: pointer;
    transition: all 0.2s;
}}
.kw-add-btn:hover {{
    background: {PRIMARY};
    color: #fff;
}}

/* ── Section Divider ──────────────────────────────────── */
.divider {{
    height: 1px;
    background: linear-gradient(90deg, transparent, #E2E8F0, transparent);
    margin: 24px 0;
}}

/* ── Stat Row ─────────────────────────────────────────── */
.stat-row {{
    display: flex;
    gap: 12px;
    margin-top: 20px;
    width: 100%;
}}
.stat-item {{
    background: #F1F5F9;
    border-radius: 8px;
    padding: 12px 8px;
    text-align: center;
    flex: 1;
}}
.stat-val {{
    font-size: 1.1rem;
    font-weight: 700;
    color: {TEXT_DARK};
}}
.stat-label {{
    font-size: 0.75rem;
    color: {TEXT_MED};
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 0.5px;
    margin-top: 4px;
}}

/* ── Streamlit overrides ──────────────────────────────── */
.stFileUploader > div > div {{
    border: 1px dashed {PRIMARY} !important;
    border-radius: 12px !important;
    background: #F8F7FF !important;
}}
.stFileUploader button {{
    background-color: {PRIMARY} !important;
    color: white !important;
    border: none !important;
    border-radius: 8px !important;
    font-weight: 600 !important;
}}
.stButton > button {{
    background: {PRIMARY} !important;
    color: #fff !important;
    border: none !important;
    border-radius: 8px !important;
    padding: 10px 24px !important;
    font-weight: 600 !important;
    font-size: 0.95rem !important;
    transition: all 0.3s ease !important;
    box-shadow: 0 4px 12px rgba(108, 99, 255, 0.15) !important;
}}
.stButton > button:hover {{
    transform: translateY(-1px) !important;
    box-shadow: 0 6px 16px rgba(108, 99, 255, 0.25) !important;
}}
.stTextArea textarea {{
    border: 1px solid #E2E8F0 !important;
    border-radius: 12px !important;
    font-family: 'Inter', sans-serif !important;
}}
.stTextArea textarea:focus {{
    border-color: {PRIMARY} !important;
    box-shadow: 0 0 0 3px rgba(108, 99, 255, 0.1) !important;
}}
</style>
""", unsafe_allow_html=True)


# ── SVG Progress Ring generator ──────────────────────────────────────────────
def svg_progress_ring(score: int, size: int = 180, stroke: int = 12) -> str:
    """Generate an SVG circular progress ring."""
    radius = (size - stroke) // 2
    circumference = 2 * 3.14159 * radius
    offset = circumference - (score / 100) * circumference

    if score >= 80:
        color = SUCCESS
        label = "Excellent"
        label_color = SUCCESS
    elif score >= 60:
        color = WARNING
        label = "Good"
        label_color = WARNING
    else:
        color = DANGER
        label = "Average"
        label_color = DANGER

    return f"""
    <div class="ring-container" style="display: flex; flex-direction: column; align-items: center; justify-content: center; width: 100%;">
        <svg width="{size}" height="{size}" viewBox="0 0 {size} {size}">
            <!-- Background circle -->
            <circle cx="{size//2}" cy="{size//2}" r="{radius}"
                    fill="none" stroke="#F1F5F9" stroke-width="{stroke}"/>
            <!-- Progress arc -->
            <circle cx="{size//2}" cy="{size//2}" r="{radius}"
                    fill="none" stroke="{color}" stroke-width="{stroke}"
                    stroke-linecap="round"
                    stroke-dasharray="{circumference}"
                    stroke-dashoffset="{offset}"
                    transform="rotate(-90 {size//2} {size//2})"
                    style="transition: stroke-dashoffset 1s ease;"/>
            <!-- Score text -->
            <text x="{size//2}" y="{size//2 - 8}"
                  text-anchor="middle" dominant-baseline="central"
                  font-family="Inter, sans-serif" font-weight="800"
                  font-size="42" fill="{TEXT_DARK}">{score}</text>
            <text x="{size//2}" y="{size//2 + 22}"
                  text-anchor="middle" dominant-baseline="central"
                  font-family="Inter, sans-serif" font-weight="600"
                  font-size="13" fill="{TEXT_LIGHT}">out of 100</text>
        </svg>
        <div style="font-size: 1.25rem; font-weight: 700; color: {label_color}; margin-top: 16px; margin-bottom: 4px; text-align: center;">{label}</div>
        <div class="ring-label" style="margin-top: 0; margin-bottom: 12px; font-size: 0.75rem; color: {TEXT_LIGHT}; font-weight: 600; text-transform: uppercase; letter-spacing: 0.5px;">ATS Compatibility Score</div>
    </div>
    """


def metric_row_html(name: str, pct: int, color: str, icon_char: str) -> str:
    """Generate an HTML row for a metric with an icon circle, progress bar, and percentage."""
    return f"""
    <div class="metric-row" style="display: flex; align-items: center; margin-bottom: 18px; gap: 16px;">
        <!-- Colored icon circle on left -->
        <div style="background-color: {color}15; color: {color}; width: 36px; height: 36px; border-radius: 50%; display: flex; align-items: center; justify-content: center; font-size: 1.1rem; font-weight: bold; flex-shrink: 0;">
            {icon_char}
        </div>
        <!-- Middle section: label & progress bar -->
        <div style="flex-grow: 1; min-width: 0;">
            <div style="font-size: 0.85rem; font-weight: 600; color: {TEXT_DARK}; margin-bottom: 6px;">{name}</div>
            <div class="progress-track" style="height: 8px; background: #F1F5F9; border-radius: 4px; overflow: hidden; position: relative; width: 100%;">
                <div class="progress-fill" style="height: 100%; border-radius: 4px; background: {color}; width: {pct}%; transition: width 0.8s ease;"></div>
            </div>
        </div>
        <!-- Percentage on right -->
        <div style="font-size: 0.9rem; font-weight: 700; color: {TEXT_DARK}; width: 40px; text-align: right; flex-shrink: 0;">
            {pct}%
        </div>
    </div>
    """


def missing_keyword_row(name: str, priority: str) -> str:
    """Generate one missing keyword row with red dot, priority badge, and + Add button."""
    priority_class = priority.lower()
    return f"""
    <div class="kw-row" style="display: flex; align-items: center; justify-content: space-between; padding: 12px 0; border-bottom: 1px solid #F1F5F9;">
        <div class="kw-info" style="display: flex; align-items: center; gap: 12px; min-width: 0; flex-grow: 1;">
            <!-- Red dot -->
            <span style="height: 8px; width: 8px; background-color: #EF4444; border-radius: 50%; display: inline-block; flex-shrink: 0;"></span>
            <!-- Keyword name -->
            <span class="kw-name" style="font-size: 0.9rem; font-weight: 600; color: {TEXT_DARK}; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; max-width: 140px;">{name}</span>
            <!-- Priority badge -->
            <span class="kw-priority {priority_class}" style="font-size: 0.72rem; font-weight: 700; padding: 3px 8px; border-radius: 12px; text-transform: uppercase; letter-spacing: 0.5px; flex-shrink: 0;">{priority}</span>
        </div>
        <!-- Add button in purple -->
        <span class="kw-add-btn" style="display: inline-block; padding: 5px 12px; border-radius: 6px; font-size: 0.78rem; font-weight: 600; background: #F3F2FF; color: {PRIMARY}; cursor: pointer; transition: all 0.2s; flex-shrink: 0;">+ Add</span>
    </div>
    """


# ══════════════════════════════════════════════════════════════════════════════
# HERO SECTION
# ══════════════════════════════════════════════════════════════════════════════

hero_left, hero_right = st.columns([1, 1], gap="large")

with hero_left:
    st.markdown("""
    <div>
        <span class="hero-badge">AI-Powered Analysis</span>
        <h1 class="hero-title">AI Resume Analyzer</h1>
        <p class="hero-sub">
            Get instant feedback on your resume's ATS compatibility, skill gaps, and actionable suggestions to land more interviews.
        </p>
    </div>
    """, unsafe_allow_html=True)

    uploaded_file = st.file_uploader(
        "Upload your resume (PDF)", type=["pdf"], key="resume_upload",
        label_visibility="collapsed",
    )

with hero_right:
    st.markdown("""
    <div style="margin-bottom: 8px;">
        <span style="font-size: 0.75rem; font-weight: 700; color: #64748B; text-transform: uppercase; letter-spacing: 1.2px;">Job Description (Optional)</span>
    </div>
    """, unsafe_allow_html=True)
    job_description = st.text_area(
        "Paste a job description for match scoring",
        height=180,
        key="jd_input",
        placeholder="Paste the full job description here for skill-gap analysis and keyword matching…",
        label_visibility="collapsed",
    )

# ── Analyse button ───────────────────────────────────────────────────────────
analyse_clicked = st.button("🔍  Analyze Resume", use_container_width=True, type="primary")

# ══════════════════════════════════════════════════════════════════════════════
# RESULTS – only shown after clicking Analyse
# ══════════════════════════════════════════════════════════════════════════════

if not analyse_clicked:
    if "results" not in st.session_state:
        st.markdown(f"""
        <div style="text-align:center; padding:60px 20px;">
            <p style="font-size:3rem;margin-bottom:8px;">📄</p>
            <p style="font-size:1.1rem;font-weight:600;color:{TEXT_DARK};">
                Upload a resume and click Analyze to get started
            </p>
            <p style="font-size:0.9rem;color:{TEXT_LIGHT};max-width:480px;margin:8px auto 0;">
                Your resume will be parsed, scored for ATS compatibility,
                and analyzed for skill gaps against a job description.
            </p>
        </div>
        """, unsafe_allow_html=True)
        st.stop()

if analyse_clicked:
    if uploaded_file is None:
        st.warning("⚠️ Please upload a PDF resume first.")
        st.stop()

    # Save to temp file
    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
        tmp.write(uploaded_file.read())
        tmp_path = tmp.name

    with st.spinner("🔍 Analyzing your resume…"):
        parsed = parse_resume(tmp_path)
        text = parsed["text"]

        if not text.strip():
            st.error("Could not extract text from the PDF. Ensure it's not image-only or password-protected.")
            Path(tmp_path).unlink(missing_ok=True)
            st.stop()

        ats_report = run_ats_check(parsed)
        all_skills = extract_skills(text)
        categories = categorise_skills(all_skills)
        freq = extract_skills_with_frequency(text)

        jd_text = job_description.strip() if job_description else None
        match_result = match_resume_to_job(text, jd_text) if jd_text else None
        tips = generate_suggestions(parsed, jd_text)

    # Store results in session state so they persist
    st.session_state["results"] = {
        "parsed": parsed,
        "text": text,
        "ats_report": ats_report,
        "skills": all_skills,
        "categories": categories,
        "freq": freq,
        "match_result": match_result,
        "tips": tips,
        "tmp_path": tmp_path,
    }

# ── Load results from session state ──────────────────────────────────────────
if "results" not in st.session_state:
    st.stop()

r = st.session_state["results"]
parsed = r["parsed"]
text = r["text"]
ats_report = r["ats_report"]
all_skills = r["skills"]
categories = r["categories"]
freq = r["freq"]
match_result = r["match_result"]
tips = r["tips"]

st.markdown('<div class="divider"></div>', unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════════════════════
# DASHBOARD ROW 1 – ATS Ring + Stats | Score Breakdown
# ══════════════════════════════════════════════════════════════════════════════

dash_left, dash_right = st.columns([1, 1.2], gap="large")

ats_score = ats_report["overall_score"]

# ── Left: ATS Ring + Rank / Market Fit ───────────────────────────────────────
with dash_left:
    st.markdown('<div class="card">', unsafe_allow_html=True)

    # Ring
    st.markdown(svg_progress_ring(ats_score), unsafe_allow_html=True)

    # Rank + Market Fit stats
    pass_ratio = ats_report["pass_count"]
    total_checks = len(ats_report["checks"])
    rank_label = "Excellent" if ats_score >= 80 else ("Good" if ats_score >= 60 else ("Fair" if ats_score >= 40 else "Needs Work"))

    market_fit = match_result["weighted_score"] if match_result else 0
    market_label = f"{market_fit}%" if match_result else "N/A"

    st.markdown(f"""
    <div class="stat-row">
        <div class="stat-item">
            <div class="stat-val">{rank_label}</div>
            <div class="stat-label">Rank</div>
        </div>
        <div class="stat-item">
            <div class="stat-val">{market_label}</div>
            <div class="stat-label">Market Fit</div>
        </div>
        <div class="stat-item">
            <div class="stat-val">{pass_ratio}/{total_checks}</div>
            <div class="stat-label">Checks Passed</div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown('</div>', unsafe_allow_html=True)

# ── Right: Score Breakdown bars ──────────────────────────────────────────────
with dash_right:
    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.markdown('<div class="card-title">Score Breakdown</div>', unsafe_allow_html=True)

    # Compute sub-scores from ATS checks
    readability_checks = [c for c in ats_report["checks"] if c["name"] in ("Bullet Points", "Formatting", "Resume Length")]
    readability_score = round(sum(c["score"] for c in readability_checks) / max(len(readability_checks), 1))

    keyword_checks = [c for c in ats_report["checks"] if c["name"] in ("Action Verbs", "Section Structure")]
    keyword_score = round(sum(c["score"] for c in keyword_checks) / max(len(keyword_checks), 1))

    impact_checks = [c for c in ats_report["checks"] if c["name"] in ("Measurable Results", "Contact Information", "Professional Email")]
    impact_score = round(sum(c["score"] for c in impact_checks) / max(len(impact_checks), 1))

    st.markdown(metric_row_html("ATS Readability", readability_score, "#10B981", "📄"), unsafe_allow_html=True)
    st.markdown(metric_row_html("Keyword Match", keyword_score, "#6C63FF", "🔑"), unsafe_allow_html=True)
    st.markdown(metric_row_html("Impact Metrics", impact_score, "#F97316", "📈"), unsafe_allow_html=True)

    # If job description provided, add similarity bar
    if match_result:
        st.markdown(metric_row_html("Job Similarity", round(match_result["similarity_score"]), "#3B82F6", "🤝"), unsafe_allow_html=True)
        st.markdown(metric_row_html("Skill Overlap", round(match_result["skill_overlap_pct"]), "#6366F1", "🧬"), unsafe_allow_html=True)

    st.markdown('</div>', unsafe_allow_html=True)

st.markdown('<div class="divider"></div>', unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════════════════════
# DASHBOARD ROW 2 – Skills Detected | Missing Keywords
# ══════════════════════════════════════════════════════════════════════════════

skills_col, keywords_col = st.columns(2, gap="large")

# ── Left: Skills Detected ────────────────────────────────────────────────────
with skills_col:
    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.markdown(f'<div class="card-title">Skills Detected ({len(all_skills)})</div>', unsafe_allow_html=True)

    for cat, items in categories.items():
        st.markdown(f"""
        <p style="font-size:0.72rem;font-weight:700;color:#94A3B8;margin:16px 0 6px;
                  text-transform:uppercase;letter-spacing:0.8px;">{cat}</p>
        """, unsafe_allow_html=True)
        pills = "".join(f'<span class="skill-pill detected">{s.title()}</span>' for s in items)
        st.markdown(pills, unsafe_allow_html=True)

    st.markdown('</div>', unsafe_allow_html=True)

# ── Right: Missing Keywords ──────────────────────────────────────────────────
with keywords_col:
    st.markdown('<div class="card">', unsafe_allow_html=True)

    if match_result:
        missing = match_result["skill_analysis"]["missing"]
        st.markdown(f'<div class="card-title">Missing Keywords ({len(missing)})</div>', unsafe_allow_html=True)

        if missing:
            rows_html = ""
            for i, kw in enumerate(missing[:12]):
                # Assign priority based on position (top ones are more important)
                if i < len(missing) * 0.33:
                    priority = "High"
                elif i < len(missing) * 0.66:
                    priority = "Medium"
                else:
                    priority = "Low"
                rows_html += missing_keyword_row(kw.title(), priority)

            st.markdown(rows_html, unsafe_allow_html=True)

            if len(missing) > 12:
                st.markdown(f"""
                <p style="text-align:center;color:{TEXT_LIGHT};font-size:0.82rem;
                          margin-top:12px;">
                    + {len(missing) - 12} more missing keywords
                </p>
                """, unsafe_allow_html=True)
        else:
            st.markdown(f"""
            <div style="text-align:center;padding:32px 0;">
                <p style="font-size:2rem;margin-bottom:8px;">🎉</p>
                <p style="font-size:0.9rem;color:{TEXT_MED};font-weight:600;">
                    No missing keywords – great match!
                </p>
            </div>
            """, unsafe_allow_html=True)
    else:
        st.markdown('<div class="card-title">Missing Keywords</div>', unsafe_allow_html=True)
        st.markdown(f"""
        <div style="text-align:center;padding:32px 0;">
            <p style="font-size:2rem;margin-bottom:8px;">📝</p>
            <p style="font-size:0.9rem;color:{TEXT_MED};font-weight:600;">
                Paste a job description above<br>to see missing keywords
            </p>
        </div>
        """, unsafe_allow_html=True)

    st.markdown('</div>', unsafe_allow_html=True)

st.markdown('<div class="divider"></div>', unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════════════════════
# DASHBOARD ROW 3 – Suggestions + Overview
# ══════════════════════════════════════════════════════════════════════════════

sugg_col, overview_col = st.columns(2, gap="large")

# ── Left: Suggestions ────────────────────────────────────────────────────────
with sugg_col:
    st.markdown('<div class="card">', unsafe_allow_html=True)
    stats = get_suggestion_stats(tips)
    st.markdown(f'<div class="card-title">Improvement Suggestions ({stats["total"]})</div>', unsafe_allow_html=True)

    if not tips:
        st.markdown(f"""
        <div style="text-align:center;padding:20px 0;">
            <p style="font-size:2rem;">✅</p>
            <p style="color:{TEXT_MED};font-weight:600;">Your resume looks great!</p>
        </div>
        """, unsafe_allow_html=True)
    else:
        for tip in tips[:8]:
            priority_class = "high" if tip["priority"] == 1 else ("medium" if tip["priority"] == 2 else "low")
            priority_text = "High" if tip["priority"] == 1 else ("Medium" if tip["priority"] == 2 else "Low")
            icon = {"ATS": "📊", "Skills": "🏷️", "Content": "📝", "Formatting": "🎨"}.get(tip["category"], "💡")

            st.markdown(f"""
            <div class="kw-row">
                <div class="kw-info" style="flex:1">
                    <span style="font-size:1.1rem">{icon}</span>
                    <span class="kw-name" style="font-size:0.82rem;font-weight:500;">{tip['message'][:80]}{'…' if len(tip['message']) > 80 else ''}</span>
                </div>
                <span class="kw-priority {priority_class}">{priority_text}</span>
            </div>
            """, unsafe_allow_html=True)

        if len(tips) > 8:
            st.markdown(f"""
            <p style="text-align:center;color:{TEXT_LIGHT};font-size:0.82rem;margin-top:12px;">
                + {len(tips) - 8} more suggestions
            </p>
            """, unsafe_allow_html=True)

    st.markdown('</div>', unsafe_allow_html=True)

# ── Right: Resume Overview ───────────────────────────────────────────────────
with overview_col:
    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.markdown('<div class="card-title">Resume Overview</div>', unsafe_allow_html=True)

    name = parsed.get("name", "Unknown")
    email = parsed.get("email") or "Not found"
    phone = parsed.get("phone") or "Not found"
    linkedin = "✅ Found" if parsed.get("linkedin") else "❌ Missing"
    github = "✅ Found" if parsed.get("github") else "–"
    years = parsed.get("years_of_experience")
    years_text = f"{years}+ years" if years else "–"
    edu = parsed.get("education", [])
    edu_text = ", ".join(edu[:2]) if edu else "–"
    sections_count = len(parsed.get("sections", {}))

    overview_items = [
        ("👤", "Name", name),
        ("📧", "Email", email),
        ("📱", "Phone", phone),
        ("🔗", "LinkedIn", linkedin),
        ("💻", "GitHub", github),
        ("📅", "Experience", years_text),
        ("🎓", "Education", edu_text),
        ("📋", "Sections", f"{sections_count} detected"),
        ("📝", "Words", str(parsed.get("word_count", 0))),
    ]

    for icon, label, value in overview_items:
        st.markdown(f"""
        <div style="display:flex;align-items:center;padding:8px 0;border-bottom:1px solid #F0F0F5;">
            <span style="font-size:1rem;width:28px;">{icon}</span>
            <span style="font-size:0.82rem;color:{TEXT_LIGHT};font-weight:600;width:90px;">{label}</span>
            <span style="font-size:0.85rem;color:{TEXT_DARK};font-weight:500;">{value}</span>
        </div>
        """, unsafe_allow_html=True)

    st.markdown('</div>', unsafe_allow_html=True)

# ── Footer ───────────────────────────────────────────────────────────────────
st.markdown(f"""
<div style="text-align:center;padding:40px 0 20px;">
    <p style="font-size:0.8rem;color:{TEXT_LIGHT};">
        Built with ❤️ using Streamlit • spaCy • NLTK • scikit-learn
    </p>
</div>
""", unsafe_allow_html=True)

# Cleanup temp file
tmp_path = r.get("tmp_path")
if tmp_path:
    Path(tmp_path).unlink(missing_ok=True)
