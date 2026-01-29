@app.get("/__version")
def version():
    return {"version": "CJ-RENDER-V1"}
