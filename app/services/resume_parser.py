import re
import pdfplumber
import docx
import tempfile
import os
from fastapi import UploadFile


# -----------------------------
# TEXT EXTRACTION + VALIDATION
# -----------------------------
def extract_text(file: UploadFile) -> str:
    suffix = os.path.splitext(file.filename)[1].lower()

    if suffix not in [".pdf", ".docx"]:
        raise ValueError("Unsupported file format. Only .pdf and .docx allowed.")

    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
        tmp.write(file.file.read())
        tmp_path = tmp.name

    text = ""

    try:
        if suffix == ".pdf":
            with pdfplumber.open(tmp_path) as pdf:
                for page in pdf.pages:
                    page_text = page.extract_text()
                    if page_text:
                        text += page_text + "\n"

        elif suffix == ".docx":
            doc = docx.Document(tmp_path)
            for para in doc.paragraphs:
                text += para.text + "\n"
    finally:
        os.unlink(tmp_path)

    return text.strip()


# -----------------------------
# EMAIL
# -----------------------------
def extract_email(text: str):
    match = re.search(
        r"[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+",
        text
    )
    return match.group() if match else None


# -----------------------------
# LINKEDIN (FULL URL)
# -----------------------------
def extract_linkedin(text: str):
    if not text:
        return None

    t = text.lower()

    # normalize common PDF artefacts
    t = re.sub(r"linkedin\s*\.\s*com", "linkedin.com", t)
    t = re.sub(r"(linkedin\.com)\s*/\s*(in|pub)\s*/\s*", r"\1/\2/", t)

    # repair broken lines
    t = re.sub(
        r"(linkedin\.com/(?:in|pub)/[a-z0-9\-]+)\s*\n\s*([a-z0-9\-]+)",
        r"\1\2",
        t
    )

    matches = re.findall(
        r"(?:https?://)?(?:www\.)?linkedin\.com/(?:in|pub)/[a-z0-9\-]+",
        t
    )

    if not matches:
        return None

    url = max(matches, key=len)

    if url.startswith("www."):
        url = "https://" + url
    if url.startswith("linkedin.com"):
        url = "https://www." + url
    if url.startswith("https://linkedin.com"):
        url = url.replace("https://linkedin.com", "https://www.linkedin.com")

    if not url.endswith("/"):
        url += "/"

    return url


# -----------------------------
# NAME (ATS SAFE)
# -----------------------------
def extract_full_name(text: str, email: str | None, filename: str) -> str:
    linkedin = extract_linkedin(text)

    # 1️⃣ LinkedIn slug (strongest)
    if linkedin:
        slug = linkedin.split("/in/")[-1].strip("/").replace("-", " ")
        slug = re.sub(r"\d+", "", slug).strip()
        if len(slug.split()) >= 2:
            return slug.title()

    # 2️⃣ Header scan (safe)
    lines = [l.strip() for l in text.splitlines() if l.strip()]
    for line in lines[:10]:
        if (
            2 <= len(line.split()) <= 6
            and line.replace(" ", "").replace(".", "").isalpha()
            and not any(x in line.lower() for x in ["resume", "profile", "engineer"])
        ):
            return line.title()

    # 3️⃣ Email fallback
    if email:
        prefix = email.split("@")[0]
        prefix = re.sub(r"\d+", "", prefix)
        prefix = prefix.replace(".", " ").replace("_", " ").replace("-", " ")
        if len(prefix.split()) >= 2:
            return prefix.title()

    # 4️⃣ Filename fallback
    name = os.path.splitext(filename)[0]
    name = re.sub(r"\d+", "", name)
    name = name.replace("_", " ").replace("-", " ")
    return name.title() if name else "Unknown Candidate"


# -----------------------------
# MASTER PARSER (STAGE 1)
# -----------------------------
def parse_resume(file: UploadFile) -> dict:
    text = extract_text(file)

    email = extract_email(text)
    linkedin = extract_linkedin(text)
    full_name = extract_full_name(text, email, file.filename)

    return {
        "fullName": full_name,
        "email": email or "",
        "linkedin": linkedin or "",
        "rawText": text
    }
