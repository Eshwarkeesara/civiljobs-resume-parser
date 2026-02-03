# api/resume.py
from fastapi import APIRouter, UploadFile, File, HTTPException
import tempfile
import os

from app.services.resume_parser import parse_resume

router = APIRouter(prefix="/api/resume", tags=["Resume"])


@router.post("/parse")
async def parse_resume_endpoint(file: UploadFile = File(...)):
    """
    API layer only.
    Saves file temporarily and delegates logic to resume_parser.
    """

    if not file.filename.lower().endswith((".pdf", ".docx")):
        raise HTTPException(status_code=400, detail="Only PDF or DOCX files are supported")

    # Create temp file
    with tempfile.NamedTemporaryFile(delete=False, suffix=file.filename) as tmp:
        contents = await file.read()
        tmp.write(contents)
        tmp_path = tmp.name

    try:
        parsed = parse_resume(tmp_path)
        return parsed
    finally:
        os.remove(tmp_path)
