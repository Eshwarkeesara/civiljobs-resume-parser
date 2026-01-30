import pdfplumber
from docx import Document
import re


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
