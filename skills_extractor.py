"""
skills_extractor.py – Identify and categorise skills from resume text.

Uses a reference dictionary (data/skills_list.txt) for keyword matching,
spaCy NER for discovering unlisted tools/products, and NLTK for text
normalisation.
"""

from pathlib import Path
import spacy
import nltk
from nltk.corpus import stopwords
from nltk.tokenize import word_tokenize

nltk.download("stopwords", quiet=True)
nltk.download("punkt", quiet=True)
nltk.download("punkt_tab", quiet=True)

nlp = spacy.load("en_core_web_sm")

SKILLS_FILE = Path(__file__).parent / "data" / "skills_list.txt"

# Common false-positive entities to filter out
FALSE_POSITIVES = {
    "the", "a", "an", "inc", "llc", "ltd", "co", "corp",
    "january", "february", "march", "april", "may", "june",
    "july", "august", "september", "october", "november", "december",
    "present", "current", "city", "state", "university",
}


def load_skills_list(path: Path = SKILLS_FILE) -> list[str]:
    """Load the reference skill list from a text file (one skill per line)."""
    if not path.exists():
        return []
    with open(path, encoding="utf-8") as f:
        return [line.strip().lower() for line in f if line.strip()]


def _normalise_text(text: str) -> str:
    """Lowercase and collapse whitespace for matching."""
    return " ".join(text.lower().split())


def extract_skills(text: str, skills_list: list[str] | None = None) -> list[str]:
    """
    Return a deduplicated, sorted list of skills found in *text*.

    Strategy
    --------
    1. Normalise the resume text to lowercase.
    2. For each skill in the reference list, check whether it appears as a
       substring (handles multi-word skills like "machine learning").
    3. Filter out any skills that are identified in the text as GPE (cities),
       DATE (dates), ORG (universities/organizations), or PERSON.
    4. Return sorted, deduplicated skills.

    Parameters
    ----------
    text : str
        The full resume text (or any section of it).
    skills_list : list[str] | None
        Explicit skill list to match against. Defaults to the bundled file.

    Returns
    -------
    list[str]
        Sorted, deduplicated skill names (lowercase).
    """
    if skills_list is None:
        skills_list = load_skills_list()

    text_normalised = _normalise_text(text)
    found: set[str] = set()

    # Dictionary-based matching
    for skill in skills_list:
        if skill in text_normalised:
            found.add(skill)

    # Filter out skills that match identified proper noun entities like GPE, DATE, ORG, PERSON
    # This prevents extracting city names, university names, dates, or names as skills.
    doc = nlp(text[:8000])  # cap for performance
    exclude_ents = set()
    for ent in doc.ents:
        if ent.label_ in ("GPE", "DATE", "ORG", "PERSON"):
            exclude_ents.add(ent.text.strip().lower())

    final_skills = set()
    for skill in found:
        if skill not in exclude_ents:
            final_skills.add(skill)

    return sorted(final_skills)


def extract_skills_with_frequency(
    text: str, skills_list: list[str] | None = None,
) -> dict[str, int]:
    """
    Return skills with their occurrence count in the text.

    Useful for identifying which skills a candidate emphasises most.
    """
    if skills_list is None:
        skills_list = load_skills_list()

    text_normalised = _normalise_text(text)
    freq: dict[str, int] = {}

    for skill in skills_list:
        count = text_normalised.count(skill)
        if count > 0:
            freq[skill] = count

    return dict(sorted(freq.items(), key=lambda x: x[1], reverse=True))


def categorise_skills(skills: list[str]) -> dict[str, list[str]]:
    """
    Bucket skills into broad categories for display.

    Categories
    ----------
    Programming Languages, Frameworks & Libraries, Cloud & DevOps,
    Data & ML, Databases, Design, Testing, Soft Skills, Other.
    """
    categories: dict[str, list[str]] = {
        "Programming Languages": [],
        "Frameworks & Libraries": [],
        "Cloud & DevOps": [],
        "Data & ML": [],
        "Databases": [],
        "Design": [],
        "Testing": [],
        "Soft Skills": [],
        "Other": [],
    }

    programming = {
        "python", "java", "javascript", "typescript", "c++", "c#",
        "ruby", "go", "rust", "swift", "kotlin", "php", "sql",
        "html", "css",
    }
    frameworks = {
        "react", "angular", "vue.js", "node.js", "express.js",
        "django", "flask", "fastapi", "spring boot", ".net",
    }
    cloud_devops = {
        "docker", "kubernetes", "aws", "azure", "google cloud",
        "git", "github", "ci/cd", "jenkins", "terraform", "ansible",
        "linux", "devops", "microservices",
    }
    data_ml = {
        "machine learning", "deep learning", "natural language processing",
        "computer vision", "tensorflow", "pytorch", "scikit-learn",
        "pandas", "numpy", "matplotlib", "data analysis",
        "data engineering", "data visualization", "power bi", "tableau",
        "excel", "rest api", "graphql", "blockchain", "solidity", "web3",
    }
    databases = {
        "mongodb", "postgresql", "mysql", "redis",
        "elasticsearch", "apache kafka", "rabbitmq",
    }
    design = {
        "graphic design", "ui/ux design", "figma",
        "adobe photoshop", "adobe illustrator",
    }
    testing = {
        "selenium", "jest", "pytest", "unit testing",
        "integration testing", "test driven development",
    }
    soft = {
        "communication", "teamwork", "leadership", "problem solving",
        "critical thinking", "time management", "adaptability",
        "creativity", "attention to detail", "customer service",
        "public speaking", "negotiation", "conflict resolution",
        "strategic planning", "agile", "scrum", "jira",
        "project management", "financial analysis", "marketing",
        "seo", "content writing",
    }

    for skill in skills:
        if skill in programming:
            categories["Programming Languages"].append(skill)
        elif skill in frameworks:
            categories["Frameworks & Libraries"].append(skill)
        elif skill in cloud_devops:
            categories["Cloud & DevOps"].append(skill)
        elif skill in data_ml:
            categories["Data & ML"].append(skill)
        elif skill in databases:
            categories["Databases"].append(skill)
        elif skill in design:
            categories["Design"].append(skill)
        elif skill in testing:
            categories["Testing"].append(skill)
        elif skill in soft:
            categories["Soft Skills"].append(skill)
        else:
            categories["Other"].append(skill)

    # Remove empty categories
    return {k: v for k, v in categories.items() if v}


def get_skill_summary(text: str) -> dict:
    """
    Convenience function returning a complete skill analysis.

    Returns dict with:
        skills            – sorted list of skill names
        categories        – dict of category → skill list
        frequency         – dict of skill → count
        total_skills      – int
        top_skills        – top 10 most-mentioned skills
    """
    skills = extract_skills(text)
    freq = extract_skills_with_frequency(text)
    top = list(freq.items())[:10]

    return {
        "skills": skills,
        "categories": categorise_skills(skills),
        "frequency": freq,
        "total_skills": len(skills),
        "top_skills": top,
    }
