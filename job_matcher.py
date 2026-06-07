"""
job_matcher.py – Compare a resume against a job description.

Uses TF-IDF vectorisation + cosine similarity (scikit-learn) for an overall
match score, NLTK text preprocessing for better token quality, and
set operations on extracted skills for skill-gap analysis.
"""

import re
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import nltk
from nltk.corpus import stopwords
from nltk.tokenize import word_tokenize
from nltk.stem import WordNetLemmatizer

from skills_extractor import extract_skills

nltk.download("wordnet", quiet=True)
nltk.download("stopwords", quiet=True)
nltk.download("punkt", quiet=True)
nltk.download("punkt_tab", quiet=True)


def _preprocess(text: str) -> str:
    """
    Clean and normalise text for TF-IDF comparison.

    Steps: lowercase → strip non-alpha → remove stopwords → lemmatise.
    """
    lemmatiser = WordNetLemmatizer()
    stop_words = set(stopwords.words("english"))

    tokens = word_tokenize(text.lower())
    tokens = [
        lemmatiser.lemmatize(t)
        for t in tokens
        if t.isalpha() and t not in stop_words and len(t) > 1
    ]
    return " ".join(tokens)


def compute_similarity(resume_text: str, job_description: str) -> float:
    """
    Return a 0–100 cosine-similarity score between the resume and the JD.

    Both texts are preprocessed (stopword removal, lemmatisation) before
    TF-IDF vectorisation with unigrams + bigrams.
    """
    processed_resume = _preprocess(resume_text)
    processed_jd = _preprocess(job_description)

    vectoriser = TfidfVectorizer(
        ngram_range=(1, 2),
        max_features=5000,
        sublinear_tf=True,       # dampens raw term-frequency
    )
    tfidf_matrix = vectoriser.fit_transform([processed_resume, processed_jd])
    score = cosine_similarity(tfidf_matrix[0:1], tfidf_matrix[1:2])[0][0]
    return round(score * 100, 2)


def skill_gap_analysis(
    resume_text: str,
    job_description: str,
    skills_list: list[str] | None = None,
) -> dict[str, list[str]]:
    """
    Compare skills found in the resume vs. the job description.

    Returns
    -------
    dict with keys:
        matching  – skills present in both
        missing   – skills in the JD but absent from the resume
        extra     – skills in the resume but not required by the JD
    """
    resume_skills = set(extract_skills(resume_text, skills_list))
    jd_skills = set(extract_skills(job_description, skills_list))

    return {
        "matching": sorted(resume_skills & jd_skills),
        "missing": sorted(jd_skills - resume_skills),
        "extra": sorted(resume_skills - jd_skills),
    }


def compute_keyword_density(resume_text: str, job_description: str) -> dict:
    """
    Check how many important JD keywords appear in the resume.

    Returns dict with:
        jd_keywords      – set of important keywords from the JD
        found_in_resume  – keywords present in the resume
        missing          – keywords absent from the resume
        density_pct      – percentage of JD keywords found in resume
    """
    stop_words = set(stopwords.words("english"))
    jd_tokens = word_tokenize(job_description.lower())
    jd_keywords = {
        t for t in jd_tokens
        if t.isalpha() and t not in stop_words and len(t) > 2
    }

    resume_lower = resume_text.lower()
    found = {kw for kw in jd_keywords if kw in resume_lower}
    missing = jd_keywords - found

    density = round(len(found) / max(len(jd_keywords), 1) * 100, 1)

    return {
        "jd_keywords": sorted(jd_keywords),
        "found_in_resume": sorted(found),
        "missing": sorted(missing),
        "density_pct": density,
    }


def compute_weighted_score(
    resume_text: str,
    job_description: str,
    skills_list: list[str] | None = None,
) -> dict:
    """
    Compute a weighted composite match score.

    Weights
    -------
    - TF-IDF cosine similarity: 40 %
    - Skill overlap percentage: 35 %
    - Keyword density:          25 %

    Returns dict with individual + composite scores.
    """
    similarity = compute_similarity(resume_text, job_description)
    gap = skill_gap_analysis(resume_text, job_description, skills_list)
    density = compute_keyword_density(resume_text, job_description)

    total_jd_skills = len(gap["matching"]) + len(gap["missing"])
    skill_overlap_pct = round(
        len(gap["matching"]) / max(total_jd_skills, 1) * 100, 1
    )

    weighted = round(
        similarity * 0.40
        + skill_overlap_pct * 0.35
        + density["density_pct"] * 0.25,
        2,
    )

    return {
        "similarity_score": similarity,
        "skill_overlap_pct": skill_overlap_pct,
        "keyword_density_pct": density["density_pct"],
        "weighted_score": weighted,
    }


def match_resume_to_job(
    resume_text: str,
    job_description: str,
    skills_list: list[str] | None = None,
) -> dict:
    """
    Full matching report: weighted score + skill gap + keyword density.

    Returns
    -------
    dict with keys:
        similarity_score    (float 0-100)
        skill_overlap_pct   (float 0-100)
        keyword_density_pct (float 0-100)
        weighted_score      (float 0-100)
        skill_analysis      (dict with matching / missing / extra)
        keyword_analysis    (dict with jd_keywords / found / missing / density)
        recommendation      (str)
    """
    scores = compute_weighted_score(resume_text, job_description, skills_list)
    analysis = skill_gap_analysis(resume_text, job_description, skills_list)
    keyword_info = compute_keyword_density(resume_text, job_description)

    ws = scores["weighted_score"]
    if ws >= 70:
        recommendation = (
            "🟢 Strong match – your resume aligns well with this role. "
            "Fine-tune the wording for even better results."
        )
    elif ws >= 45:
        recommendation = (
            "🟡 Moderate match – tailor your resume to highlight relevant "
            "experience and close the skill gaps listed below."
        )
    else:
        recommendation = (
            "🔴 Weak match – significant gaps exist. Focus on acquiring "
            "missing skills or rewrite to emphasise transferable experience."
        )

    return {
        **scores,
        "skill_analysis": analysis,
        "keyword_analysis": keyword_info,
        "recommendation": recommendation,
    }
