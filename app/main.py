from fastapi import FastAPI, UploadFile, File

app = FastAPI(title="Civil Jobs Resume Parser")

@app.get("/")
def health():
    return {"status": "ok"}

@app.post("/upload-test")
async def upload_test(file: UploadFile = File(...)):
    return {
        "filename": file.filename,
        "content_type": file.content_type
    }
