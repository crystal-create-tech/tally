from fastapi import FastAPI
app = FastAPI(title="Tally")

@app.get("/health")
def health_check():
    return {"status": "ok"}