from fastapi import APIRouter, UploadFile, File

router = APIRouter()

@router.post("/upload-test")
async def upload_test(file: UploadFile = File(...)):
    
return {
    "filename": file.filename,
    "parsed_data": parsed,
    
}
