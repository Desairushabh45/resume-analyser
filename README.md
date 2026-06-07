# 🤖 AI Resume Analyzer

An intelligent resume analysis tool built with Python, spaCy, NLTK, 
and Streamlit that helps job seekers optimize their resumes.

## ✨ Features
- 📄 PDF resume upload and text extraction
- 🎯 ATS compatibility scoring
- 🛠️ Skills detection by category
- 📊 Job description match scoring
- 🔍 Missing keywords identification
- 💡 Improvement suggestions

## 🚀 Live Demo
[Click here to try it](YOUR_STREAMLIT_LINK)

## 🛠️ Tech Stack
- Python 3
- spaCy & NLTK (NLP)
- Scikit-learn (TF-IDF, Cosine Similarity)
- Streamlit (UI)
- pdfplumber (PDF parsing)

## ⚙️ Installation
1. Clone the repo
   ```bash
   git clone https://github.com/Desairushabh45/resume-analyser.git
   cd resume-analyser
   ```

2. Install dependencies
   ```bash
   pip install -r requirements.txt
   python -m spacy download en_core_web_sm
   ```

3. Run the app
   ```bash
   python -m streamlit run app.py
   ```

## 📁 Project Structure
- app.py — Main Streamlit UI
- parser.py — PDF text extraction
- skills_extractor.py — Skills detection
- job_matcher.py — Job match scoring
- ats_checker.py — ATS compatibility check
- suggestions.py — Improvement suggestions
- data/skills_list.txt — Skills database

## 👨‍💻 Author
Desairushabh45
