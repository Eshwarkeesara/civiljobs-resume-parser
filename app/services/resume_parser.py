import pdfplumber
from docx import Document
import re
from typing import Optional

def extract_text_from_pdf(path: str) -> str:
    text = ""
    with pdfplumber.open(path) as pdf:
        for page in pdf.pages:
            page_text = page.extract_text()
            if page_text:
                text += page_text + "\n"
    return text


def extract_text_from_docx(path: str) -> str:
    doc = Document(path)
    return "\n".join(p.text for p in doc.paragraphs)

def clean_name(name: str) -> str:
    name = re.sub(r'[^A-Za-z\s]', '', name)
    name = re.sub(r'\s+', ' ', name).strip()
    return name.title()


def extract_full_name(
    text: str,
    email: Optional[str],
    linkedin_url: Optional[str],
    filename: str,
    nlp
) -> str:
    # 1️⃣ Try top lines (most reliable)
    lines = [l.strip() for l in text.splitlines() if l.strip()]
    for line in lines[:5]:
        if (
            2 <= len(line.split()) <= 5
            and not any(word in line.lower() for word in [
                "resume", "curriculum", "profile", "engineer",
                "consultant", "summary"
            ])
        ):
            return clean_name(line)

    # 2️⃣ spaCy PERSON entity
    doc = nlp(text)
    for ent in doc.ents:
        if ent.label_ == "PERSON":
            return clean_name(ent.text)

    # 3️⃣ Email fallback
    if email:
        prefix = email.split("@")[0].replace(".", " ").replace("_", " ")
        if len(prefix.split()) >= 2:
            return clean_name(prefix)

    # 4️⃣ LinkedIn fallback
    if linkedin_url:
        slug = linkedin_url.rstrip("/").split("/")[-1].replace("-", " ")
        if len(slug.split()) >= 2:
            return clean_name(slug)

    # 5️⃣ Filename fallback (GUARANTEED)
    name = re.sub(r'\.(pdf|docx)$', '', filename, flags=re.I)
    name = re.sub(r'\d+', '', name)
    name = name.replace("_", " ").replace("-", " ")
    return clean_name(name) or "Unknown Candidate"

def extract_email(text: str):
    match = re.search(
        r"[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+",
        text
    )
    return match.group() if match else None


def extract_phone(text: str):
    matches = re.findall(r"(?:\+91[-\s]?)?[6-9]\d{9}", text)
    return matches[0] if matches else None


def extract_education(text: str):
    education = []
    keywords = ["diploma", "b.tech", "btech", "m.tech", "mtech"]

    for line in text.lower().split("\n"):
        if any(k in line for k in keywords):
            education.append(line.strip())

    return education


def parse_resume(file_path: str):

    if file_path.endswith(".pdf"):
        text = extract_text_from_pdf(file_path)
    elif file_path.endswith(".docx"):
        text = extract_text_from_docx(file_path)
    else:
        return {"error": "Unsupported format"}

    return {
        "email": extract_email(text),
        "phone": extract_phone(text),
        "education_raw": extract_education(text),
        "text_preview": text[:500]
    }
