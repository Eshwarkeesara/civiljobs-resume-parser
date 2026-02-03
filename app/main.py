# main.py
from fastapi import FastAPI
from app.api.resume import router as resume_router

app = FastAPI(title="Resume Parser API")

app.include_router(resume_router)

@app.get("/")
def health():
    return {"status": "ok"}

