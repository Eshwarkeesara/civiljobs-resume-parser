from fastapi import APIRouter, UploadFile, File

router = APIRouter()

@router.post("/resume/parse")
async def parse_resume(file: UploadFile = File(...)):
    return {"status": "ok"}

