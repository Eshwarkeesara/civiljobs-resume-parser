from fastapi import APIRouter, UploadFile, File
import tempfile
import shutil
from app.services.resume_parser import parse_resume

router = APIRouter()

@router.post("/resume/parse")
async def parse_resume_api(file: UploadFile = File(...)):
    suffix = "." + file.filename.split(".")[-1]

    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
        shutil.copyfileobj(file.file, tmp)
        tmp_path = tmp.name

    parsed = parse_resume(tmp_path)

    return {
        "filename": file.filename,
        "parsed_data": parsed
    }
