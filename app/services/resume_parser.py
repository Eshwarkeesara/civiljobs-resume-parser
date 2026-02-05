import re
import pdfplumber
import docx
import tempfile
import os
import unicodedata
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
            return normalize_text(text)        
        elif suffix == ".docx":
            doc = docx.Document(tmp_path)
            for para in doc.paragraphs:
                text += para.text + "\n"
            return normalize_text(text)
        else:

            raise ValueError("Unsupported file format (PDF / DOCX only)")
        
    finally:
        os.unlink(tmp_path)

    
    # ------------------------------
    # Normalize text
    # ------------------------------
    
def normalize_text(text: str) -> str:
    text = unicodedata.normalize("NFKC", text)

    text = text.replace("\r\n", "\n").replace("\r", "\n")
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n{2,}", "\n", text)

    text = "\n".join(line.strip() for line in text.split("\n"))

    return text.strip()

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


def extract_linkedin_url(text: str):
    """
    Extracts FULL canonical LinkedIn profile URL.
    Handles line breaks, hyphen wraps, and partial URLs from PDFs.
    """

    if not text:
        return None

    # -------------------------------------------------
    # 1️⃣ Normalize text to repair broken LinkedIn URLs
    # -------------------------------------------------

    # Join lines broken after hyphens (PDF artifact)
    repaired_text = re.sub(
        r"(linkedin\.com/in/[A-Za-z0-9\-]+)-\s*\n\s*([A-Za-z0-9\-]+)",
        r"\1\2",
        text,
        flags=re.IGNORECASE
    )

    # Remove line breaks inside linkedin URLs
    repaired_text = re.sub(
        r"(linkedin\.com/in/[A-Za-z0-9\-]+)\s*\n\s*([A-Za-z0-9\-]+)",
        r"\1\2",
        repaired_text,
        flags=re.IGNORECASE
    )

    # -------------------------------------------------
    # 2️⃣ Extract ALL candidate LinkedIn URLs
    # -------------------------------------------------
    urls = re.findall(
        r"(?:https?:\/\/)?(?:www\.)?linkedin\.com\/in\/[A-Za-z0-9\-]+",
        repaired_text,
        flags=re.IGNORECASE
    )

    if not urls:
        return None

    # -------------------------------------------------
    # 3️⃣ Pick the LONGEST one (most complete)
    # -------------------------------------------------
    url = max(urls, key=len)

    # -------------------------------------------------
    # 4️⃣ Canonicalize
    # -------------------------------------------------
    url = url.lower()

    if not url.startswith("http"):
        url = "https://" + url.lstrip("/")

    if not url.startswith("https://www."):
        url = url.replace("https://linkedin.com", "https://www.linkedin.com")

    # Remove trailing junk (just in case)
    url = re.sub(r"[^\w\-\/:.\?=#]+$", "", url)

    # Ensure trailing slash
    if not url.endswith("/"):
        url += "/"

    return url

# -------------------------------------------------
# NAME TOKEN EXTRACTION (ANCHORS)
# -------------------------------------------------
def get_name_tokens(email=None, linkedin_url=None):
    """
    Extracts identity tokens ONLY from email / LinkedIn
    """
    tokens = set()

    if linkedin_url:
        m = re.search(r"linkedin\.com\/in\/([^/?]+)", linkedin_url.lower())
        if m:
            slug = re.sub(r"\d+", "", m.group(1))
            parts = re.split(r"[-_]", slug)
            tokens.update(p for p in parts if len(p) > 1)

    if email:
        username = email.split("@")[0].lower()
        parts = re.split(r"[._-]", username)
        tokens.update(p for p in parts if len(p) > 1 and not p.isdigit())

    return tokens


def is_human_name_line(line: str) -> bool:
    words = line.split()
    return (
        2 <= len(words) <= 6
        and all(w.replace(".", "").isalpha() for w in words)
        and not line.isupper()
    )

def clean_name_line(line: str) -> str:
    """
    Removes leading labels accidentally merged into name line
    e.g. 'Contact G M T Sai Kumar' → 'G M T Sai Kumar'
    """
    LABELS = [
        "contact",
        "profile",
        "resume",
        "name"
    ]

    parts = line.split()
    while parts and parts[0].lower() in LABELS:
        parts.pop(0)

    return " ".join(parts)

# -----------------------------
# NAME (GUARANTEED)
# -----------------------------
def extract_full_name(
    text: str,
    email: str | None,
    linkedin_url: str | None
) -> str | None:
    """
    RULE:
    - NEVER guess names from prose
    - ONLY accept names anchored by LinkedIn / Email tokens
    """

    tokens = get_name_tokens(email=email, linkedin_url=linkedin_url)

    if not tokens:
        return None

    lines = [l.strip() for l in text.splitlines() if l.strip()]

    # Only scan header zone
    candidate_zone = []
    for line in lines:
        if line.lower().startswith("experience"):
            break
        candidate_zone.append(line)

    for line in candidate_zone:
        low = line.lower()

        if not is_human_name_line(line):
            continue

        # Require at least TWO token matches
        if sum(t in low for t in tokens) >= 2:
            return clean_name_line(line).title()

    return None


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

    linkedin_url = extract_linkedin_url(text)

    full_name = extract_full_name(text, email, linkedin_url)

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
        "linkedinURL": linkedin_url or "",
        "education": [
            {
                "qualification": list(education_levels),
                "score": education_score
            }
        ] 
        if education_levels else [],
        "skills": skills,
        "totalExperienceYears": experience_years,
        "confidenceScore": confidence
    }
