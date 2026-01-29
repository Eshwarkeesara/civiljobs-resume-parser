from fastapi import FastAPI

# ✅ app must be defined FIRST
app = FastAPI(title="Civil Jobs Resume Parser")

# ✅ then routes can reference `app`
@app.get("/")
def health():
    return {"status": "ok"}