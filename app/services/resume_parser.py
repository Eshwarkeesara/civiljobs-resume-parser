import re
import pdfplumber
import docx
import tempfile
import os
from fastapi import UploadFile

from app.domain.education import detect_education_levels
from app.domain.education_score import score_education
from app.domain.skills import extract_skills


# -----------------------------
# TEXT EXTRACTION
# -----------------------------
def extract_text(file: UploadFile) -> str:
    suffix = os.path.splitext(file.filename)[1].lower()

    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
        tmp.write(file.file.read())
        tmp_path = tmp.name

    text = ""

    try:
        if suffix == ".pdf":
            with pdfplumber.open(tmp_path) as pdf:
                for page in pdf.pages:
                    if page.extract_text():
                        text += page.extract_text() + "\n"

        elif suffix == ".docx":
            doc = docx.Document(tmp_path)
            for para in doc.paragraphs:
                text += para.text + "\n"
    finally:
        os.unlink(tmp_path)

    return text.strip()


# -----------------------------
# NAME (GUARANTEED)
# -----------------------------
def extract_full_name(text: str, email: str | None, filename: str) -> str:
    lines = [l.strip() for l in text.splitlines() if l.strip()]

    for line in lines[:10]:
        if (
            2 <= len(line.split()) <= 6
            and line.replace(" ", "").isalpha()
            and not line.isupper()
            and not any(x in line.lower() for x in ["resume", "profile", "engineer"])
        ):
            return line.title()

    if email:
        prefix = email.split("@")[0].replace(".", " ").replace("_", " ")
        if len(prefix.split()) >= 2:
            return prefix.title()

    name = os.path.splitext(filename)[0].replace("_", " ").replace("-", " ")
    return name.title() if name else "Unknown Candidate"


# -----------------------------
# CONTACT
# -----------------------------
def extract_email(text: str):
    match = re.search(
        r"[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+",
        text
    )
    return match.group() if match else None


def extract_phone(text: str):
    match = re.search(r"(?:\+91[-\s]?)?[6-9]\d{9}", text)
    return match.group() if match else None


# -----------------------------
# EXPERIENCE
# -----------------------------
def extract_total_experience_years(text: str):
    match = re.search(r"(\d+)\s*(yrs|years)", text.lower())
    return int(match.group(1)) if match else None


# -----------------------------
# MASTER PARSER
# -----------------------------
def parse_resume(file: UploadFile) -> dict:
    text = extract_text(file)

    email = extract_email(text)
    phone = extract_phone(text)

    full_name = extract_full_name(text, email, file.filename)

    education_levels = detect_education_levels(text)
    education_score = score_education(education_levels)

    experience_years = extract_total_experience_years(text)
    skills = extract_skills(text)

    confidence = 0
    if full_name:
        confidence += 25
    if email or phone:
        confidence += 20
    if education_score > 0:
        confidence += 30
    if experience_years:
        confidence += 25

    confidence = min(confidence, 100)

    return {
        "fullName": full_name,
        "email": email or "",
        "phone": phone or "",
        "education": [
            {
                "qualification": list(education_levels),
                "score": education_score
            }
        ] if education_levels else [],
        "skills": skills,
        "totalExperienceYears": experience_years,
        "confidenceScore": confidence
    }
