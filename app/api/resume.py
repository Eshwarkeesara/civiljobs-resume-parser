from fastapi import APIRouter, UploadFile, File
from app.services.resume_parser import extract_full_name
from app.services.education_scoring import score_education
from app.services.text_extraction import extract_text  # or wherever text extraction is
from app.core.nlp import nlp  # your spaCy loader

router = APIRouter(prefix="/api/resume", tags=["Resume"])


@router.post("/parse")
async def parse_resume(file: UploadFile = File(...)):
    # 1️⃣ Extract raw text
    resume_text = extract_text(file)

    # 2️⃣ Extract basic contact info (however you already do it)
    email = extract_email(resume_text)
    phone = extract_phone(resume_text)
    linkedin_url = extract_linkedin(resume_text)

    # 3️⃣ GUARANTEED full name extraction
    full_name = extract_full_name(
        text=resume_text,
        email=email,
        linkedin_url=linkedin_url,
        filename=file.filename,
        nlp=nlp
    )

    # 4️⃣ Education detection & scoring
    education_levels = detect_education_levels(resume_text)
    education_score = score_education(education_levels)

    education = [
        {
            "qualification": list(education_levels),
            "score": education_score
        }
    ] if education_levels else []

    # 5️⃣ Confidence score (simple for now)
    confidence = 0
    if full_name: confidence += 20
    if email: confidence += 20
    if phone: confidence += 20
    if education_score > 0: confidence += 20

    confidence = min(confidence, 100)

    # 6️⃣ FINAL RESPONSE (Lovable-compatible)
    return {
        "fullName": full_name,
        "email": email or "",
        "phone": phone or "",
        "location": "",
        "linkedinUrl": linkedin_url or "",
        "summary": "",
        "education": education,
        "experience": [],
        "skills": [],
        "totalExperienceYears": None,
        "confidenceScore": confidence
    }

