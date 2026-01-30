from fastapi import APIRouter, UploadFile, File

router = APIRouter()

@router.post("/upload-test")
async def upload_test(file: UploadFile = File(...)):
    
normalized_levels = normalize_education(parsed["education_raw"])
edu_score = education_score(normalized_levels)

return {
    "filename": file.filename,
    "parsed_data": parsed,
    "education": {
        "levels": sorted(normalized_levels),
        "score": edu_score,
        "rationale": "Score based on qualification combination"
    }
}
