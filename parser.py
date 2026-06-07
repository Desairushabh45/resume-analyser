"""
parser.py – Extract text, contact info, and sections from a PDF resume.

Uses pdfplumber for PDF text extraction, spaCy NER for name recognition,
NLTK for tokenization, and regex for contact detail extraction.
"""

import re
import pdfplumber
import spacy
import nltk
from nltk.tokenize import sent_tokenize, word_tokenize

# Download required NLTK data (silent if already present)
nltk.download("punkt", quiet=True)
nltk.download("punkt_tab", quiet=True)
nltk.download("stopwords", quiet=True)
nltk.download("averaged_perceptron_tagger", quiet=True)

# Load spaCy English model
nlp = spacy.load("en_core_web_sm")

# ── Regex patterns ───────────────────────────────────────────────────────────
EMAIL_RE = re.compile(r"[\w.+-]+@[\w-]+\.[\w.-]+")
PHONE_RE = re.compile(
    r"(\+?\d{1,3}[-.\s]?)?(\(?\d{2,4}\)?[-.\s]?)?\d{3,4}[-.\s]?\d{4}"
)
LINKEDIN_RE = re.compile(r"(?:https?://)?(?:www\.)?linkedin\.com/in/[\w-]+", re.IGNORECASE)
GITHUB_RE = re.compile(r"(?:https?://)?(?:www\.)?github\.com/[\w-]+", re.IGNORECASE)
PORTFOLIO_RE = re.compile(r"(?:https?://)?[\w.-]+\.\w{2,}/?\S*", re.IGNORECASE)
YEARS_EXP_RE = re.compile(r"(\d+)\+?\s*(?:years?|yrs?)\s*(?:of\s+)?(?:experience)?", re.IGNORECASE)

# Education degree patterns
DEGREE_RE = re.compile(
    r"\b(Ph\.?D|M\.?S\.?|M\.?A\.?|B\.?S\.?|B\.?A\.?|B\.?E\.?|B\.?Tech|M\.?Tech|MBA|"
    r"Bachelor|Master|Doctorate|Associate|Diploma)\b",
    re.IGNORECASE,
)

# Common resume section headings (lowercase, without trailing colons)
SECTION_HEADINGS = {
    "summary", "professional summary", "executive summary",
    "objective", "career objective",
    "experience", "work experience", "professional experience", "employment history",
    "education", "academic background", "qualifications",
    "skills", "technical skills", "core competencies", "key skills",
    "projects", "personal projects", "academic projects",
    "certifications", "licenses", "professional certifications",
    "awards", "achievements", "honors", "honours",
    "publications", "research",
    "interests", "hobbies",
    "references",
    "languages",
    "volunteer", "volunteer experience",
    "training", "professional development",
    "extracurricular", "extracurricular activities",
}


def extract_text_from_pdf(pdf_path: str) -> str:
    """Return the full text content of a PDF file, page by page."""
    text_parts: list[str] = []
    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages:
            page_text = page.extract_text()
            if page_text:
                text_parts.append(page_text)
    return "\n".join(text_parts)


def extract_name(text: str) -> str:
    """
    Use spaCy NER to find the most likely person name.

    Scans the first 500 characters (names are typically at the top).
    Falls back to the first non-empty line if NER fails.
    """
    doc = nlp(text[:500])
    for ent in doc.ents:
        if ent.label_ == "PERSON":
            return ent.text.strip()
    # Fallback: first non-empty, non-email line
    for line in text.splitlines():
        stripped = line.strip()
        if stripped and not EMAIL_RE.search(stripped) and not PHONE_RE.search(stripped):
            return stripped
    return "Unknown"


def extract_email(text: str) -> str | None:
    """Return the first email address found."""
    match = EMAIL_RE.search(text)
    return match.group() if match else None


def extract_phone(text: str) -> str | None:
    """Return the first phone number found."""
    match = PHONE_RE.search(text)
    return match.group().strip() if match else None


def extract_linkedin(text: str) -> str | None:
    """Return the first LinkedIn profile URL found."""
    match = LINKEDIN_RE.search(text)
    return match.group() if match else None


def extract_github(text: str) -> str | None:
    """Return the first GitHub profile URL found."""
    match = GITHUB_RE.search(text)
    return match.group() if match else None


def extract_years_of_experience(text: str) -> int | None:
    """
    Extract explicitly stated years of experience.

    Looks for patterns like '5+ years of experience', '3 yrs experience', etc.
    """
    matches = YEARS_EXP_RE.findall(text)
    if matches:
        return max(int(m) for m in matches)
    return None


def extract_education(text: str) -> list[str]:
    """Extract degree mentions from the resume text."""
    matches = DEGREE_RE.findall(text)
    return list(dict.fromkeys(matches))  # deduplicate, preserve order


def extract_sections(text: str) -> dict[str, str]:
    """
    Split resume text into labelled sections based on heading detection.

    Strategy:
    1. Walk through each line.
    2. If the line (stripped, lowercased, colon-removed) matches a known
       section heading, start a new section.
    3. Accumulate subsequent lines into that section's body.

    Returns a dict mapping lowercase section name → body text.
    """
    lines = text.splitlines()
    sections: dict[str, str] = {}
    current_section: str | None = None
    buffer: list[str] = []

    for line in lines:
        cleaned = line.strip().lower().rstrip(":")
        if cleaned in SECTION_HEADINGS:
            if current_section is not None:
                sections[current_section] = "\n".join(buffer).strip()
            current_section = cleaned
            buffer = []
        else:
            buffer.append(line)

    # Save the final section
    if current_section is not None:
        sections[current_section] = "\n".join(buffer).strip()

    return sections


def compute_word_count(text: str) -> int:
    """Return the word count using NLTK tokenization."""
    tokens = word_tokenize(text)
    return len([t for t in tokens if t.isalnum()])


def compute_sentence_count(text: str) -> int:
    """Return the sentence count using NLTK."""
    return len(sent_tokenize(text))


def parse_resume(pdf_path: str) -> dict:
    """
    High-level entry point: parse a PDF resume into structured data.

    Returns
    -------
    dict with keys:
        text, name, email, phone, linkedin, github,
        years_of_experience, education, sections,
        word_count, sentence_count
    """
    text = extract_text_from_pdf(pdf_path)
    return {
        "text": text,
        "name": extract_name(text),
        "email": extract_email(text),
        "phone": extract_phone(text),
        "linkedin": extract_linkedin(text),
        "github": extract_github(text),
        "years_of_experience": extract_years_of_experience(text),
        "education": extract_education(text),
        "sections": extract_sections(text),
        "word_count": compute_word_count(text),
        "sentence_count": compute_sentence_count(text),
    }
