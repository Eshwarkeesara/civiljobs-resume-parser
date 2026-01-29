from fastapi import FastAPI
from app.api.resume import router

app = FastAPI(title="Civil Jobs Resume Parser")

app.include_router(router)
