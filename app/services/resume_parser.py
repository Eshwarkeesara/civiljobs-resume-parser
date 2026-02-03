# services/resume_parser.py

import os
import re
from typing import Optional, Dict, Any, List
from urllib.parse import urlparse

import pdfplumber
from docx import Document


# =====================================================
# Stage 1.1 — File Validation + Text Extraction
# =====================================================

SUPPORTED_EXTENSIONS = {".pdf", ".docx"}


def extract_text_from_path(file_path: str) -> str:
    ext = os.path.splitext(file_path)[1].lower()

    if ext not in SUPPORTED_EXTENSIONS:
        raise ValueError("Unsupported file type. Only PDF and DOCX allowed.")

    if ext == ".pdf":
        return _extract_pdf_text(file_path)

    if ext == ".docx":
        return _extract_docx_text(file_path)

    return ""


def _extract_pdf_text(file_path: str) -> str:
    chunks: List[str] = []
    with pdfplumber.open(file_path) as pdf:
        for page in pdf.pages:
            text = page.extract_text() or ""
            if text.strip():
                chunks.append(text)
    return normalize_text("\n".join(chunks))


def _extract_docx_text(file_path: str) -> str:
    doc = Document(file_path)
    paragraphs = [p.text for p in doc.paragraphs if p.text.strip()]
    return normalize_text("\n".join(paragraphs))


def normalize_text(text: str) -> str:
    text = text.replace("\r", "\n")
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n{2,}", "\n", text)
    return text.strip()


# =====================================================
# Stage 1.2 — Email Extraction
# =====================================================

EMAIL_REGEX = re.compile(
    r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}"
)


def extract_email(text: str) -> Optional[str]:
    match = EMAIL_REGEX.search(text)
    return match.group(0) if match else None


# =====================================================
# Stage 1.3 — LinkedIn URL (ATS-Grade, Universal)
# =====================================================

def extract_linkedin_url(text: str) -> Optional[str]:
    if not text:
        return None

    # Normalize common PDF artifacts
    t = text.lower()
    t = re.sub(r"linkedin\s*\.\s*com", "linkedin.com", t)
    t = re.sub(r"(linkedin\.com)\s*/\s*(in|pub)\s*/\s*", r"\1/\2/", t)

    # Repair line breaks inside profile slug
    t = re.sub(
        r"(linkedin\.com/(?:in|pub)/[a-z0-9\-]+)\s*\n\s*([a-z0-9\-]+)",
        r"\1\2",
        t
    )

    # Broad candidate extraction
    candidates = re.findall(
        r"(?:https?://)?(?:www\.)?linkedin\.com/(?:in|pub)/[a-z0-9\-]+",
        t
    )

    if not candidates:
        return None

    # Choose the longest (most complete)
    raw = max(candidates, key=len)

    # Canonicalize
    if raw.startswith("www."):
        raw = "https://" + raw
    if raw.startswith("linkedin.com"):
        raw = "https://www." + raw
    if raw.startswith("https://linkedin.com"):
        raw = raw.replace("https://linkedin.com", "https://www.linkedin.com")

    parsed = urlparse(raw)
    clean = f"https://{parsed.netloc}{parsed.path}"

    if not clean.endswith("/"):
        clean += "/"

    return clean


# =====================================================
# Stage 1.4 — Name Extraction (Evidence-Based)
# =====================================================

NAME_STOPWORDS = {"resume", "profile", "curriculum", "vitae", "cv", "contact"}


def extract_full_name(
    text: str,
    email: Optional[str],
    linkedin_url: Optional[str],
    filename: str
) -> Optional[str]:

    # ---- 1️⃣ Strongest signal: LinkedIn slug ----
    if linkedin_url:
        name = _name_from_linkedin(linkedin_url)
        if name:
            return name

    # ---- 2️⃣ Second signal: Email username ----
    if email:
        name = _name_from_email(email)
        if name:
            return name

    # ---- 3️⃣ Header scan (ATS-safe fallback) ----
    lines = [l.strip() for l in text.splitlines() if l.strip()]
    header_zone = lines[:25]

    for line in header_zone:
        cleaned = _clean_name_line(line)
        if _looks_like_person_name(cleaned):
            return cleaned

    # ---- 4️⃣ Last resort: filename ----
    return _name_from_filename(filename)


def _name_from_linkedin(linkedin_url: str) -> Optional[str]:
    m = re.search(r"/(in|pub)/([^/]+)/?", linkedin_url)
    if not m:
        return None

    slug = re.sub(r"\d+", "", m.group(2))
    parts = [p for p in re.split(r"[-_]", slug) if len(p) > 1]

    if len(parts) < 2:
        return None

    return " ".join(p.capitalize() for p in parts)


def _name_from_email(email: str) -> Optional[str]:
    user = email.split("@")[0]
    user = re.sub(r"\d+", "", user)
    parts = [p for p in re.split(r"[._-]", user) if len(p) > 1]

    if len(parts) < 2:
        return None

    return " ".join(p.capitalize() for p in parts)


def _clean_name_line(line: str) -> str:
    parts = line.split()
    while parts and parts[0].lower() in NAME_STOPWORDS:
        parts.pop(0)
    return " ".join(parts).title()


def _looks_like_person_name(name: str) -> bool:
    if not name:
        return False

    words = name.split()
    if not (2 <= len(words) <= 6):
        return False

    if not all(w.replace(".", "").isalpha() for w in words):
        return False

    lowered = name.lower()
    if any(x in lowered for x in [" in ", " for ", " with ", " and "]):
        return False

    return True


def _name_from_filename(filename: str) -> Optional[str]:
    base = os.path.splitext(filename)[0]
    base = re.sub(r"\d+", "", base)
    base = base.replace("_", " ").replace("-", " ").strip()
    return base.title() if len(base.split()) >= 2 else None


# =====================================================
# Stage-1 Master Orchestrator (LOCKED)
# =====================================================

def parse_resume_stage_1(
    file_path: str,
    original_filename: str
) -> Dict[str, Any]:

    text = extract_text_from_path(file_path)

    email = extract_email(text)
    linkedin = extract_linkedin_url(text)
    full_name = extract_full_name(text, email, linkedin, original_filename)

    return {
        "fullName": full_name or "",
        "email": email or "",
        "linkedin": linkedin or "",
        "rawText": text
    }
