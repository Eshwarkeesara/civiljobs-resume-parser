from fastapi import FastAPI, UploadFile, File, HTTPException
import tempfile, shutil

# Core services
from app.services.resume_parser import parse_resume

# Domain logic
from app.domain.education import normalize_education
from app.domain.education_score import education_score

app = FastAPI(title="Civil Jobs Resume Parser")

# Health check (infra)
@app.get("/")
def health():
    return {"status": "ok"}


# Main business endpoint
@app.post("/api/resume/parse")
async def parse_resume_api(file: UploadFile = File(...)):

    # 1️⃣ Validate input
    if not file.filename.lower().endswith((".pdf", ".docx")):
        raise HTTPException(
            status_code=400,
            detail="Only PDF or DOCX resumes are supported"
        )

    # 2️⃣ Persist file temporarily
    suffix = "." + file.filename.split(".")[-1]
    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
        shutil.copyfileobj(file.file, tmp)
        temp_path = tmp.name

    # 3️⃣ Parse resume (text + raw signals)
    parsed_data = parse_resume(temp_path)

    # 4️⃣ Normalize education
    edu_levels = normalize_education(parsed_data["education_raw"])

    # 5️⃣ Score education
    edu_score = education_score(edu_levels)

    # 6️⃣ Build final response (API contract)
    return {
        "filename": file.filename,
        "parsed_data": parsed_data,
        "education": {
            "levels": sorted(list(edu_levels)),
            "score": edu_score,
            "rationale": "Scored based on qualification combination"
        }
    }
