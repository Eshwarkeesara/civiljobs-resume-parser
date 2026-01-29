from fastapi import FastAPI
from app.api.resume import router as resume_router

app = FastAPI(title="Civil Jobs Resume Parser")
app.include_router(resume_router, prefix="/api")
