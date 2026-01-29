from fastapi import FastAPI

app = FastAPI(title="Civil Jobs Resume Parser")

@app.get("/__version")
def version():
    return {"version": "UPLOAD_TEST_V1"}
