# backend/app/server.py
from fastapi import FastAPI
from app.api.v1 import router as v1_router
# import attach_agent so it registers its route onto v1_router
try:
    from app.api import attach_agent  # noqa: F401
except Exception:
    pass

app = FastAPI(title="Detective Backend (server)")

app.include_router(v1_router, prefix="/api/v1")

@app.get("/")
def home():
    return {"status": "backend running (server)"}
