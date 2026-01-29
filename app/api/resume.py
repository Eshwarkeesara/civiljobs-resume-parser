from fastapi import APIRouter, UploadFile, File
import shutil
import uuid
from app.services.resume_parser import ResumeParserService

router = APIRouter()
parser = ResumeParserService()

@router.post("/resume/parse")
async def parse_resume(file: UploadFile = File(...)):
    temp_path = f"/tmp/{uuid.uuid4()}_{file.filename}"

    with open(temp_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    return parser.parse(temp_path)
