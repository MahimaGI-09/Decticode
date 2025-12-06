# backend/app/main.py
from fastapi import FastAPI
from app.api.v1 import router as v1_router

app = FastAPI(title="Detective Backend")

app.include_router(v1_router, prefix="/api/v1")

@app.get("/")
def home():
    return {"status": "backend running"}
