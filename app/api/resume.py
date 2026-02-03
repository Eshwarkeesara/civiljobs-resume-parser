from fastapi import APIRouter, UploadFile, File, HTTPException
from app.services.resume_parser import parse_resume 

router = APIRouter(prefix="/api/resume", tags=["Resume"]) 

@router.post("/parse") 
async  def parse_resume_endpoint(file: UploadFile = File(...)):
    
 """ 
    API layer only. Delegates all logic to resume_parser.
 """ 
 
if not file.filename.lower().endswith((".pdf", ".docx")):
        raise HTTPException(status_code=400, detail="Only PDF or DOCX files are supported")
     
parsed = parse_resume(file) 
return parsed

