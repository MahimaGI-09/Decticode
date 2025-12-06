# backend/app/api/agent_routes.py
from fastapi import APIRouter, HTTPException
from app.core import agent

router = APIRouter()

@router.post("/agent/run")
def agent_run(payload: dict):
    case_id = payload.get("case_id")
    instruction = payload.get("instruction", "Investigate and provide timeline and suspects.")
    if not case_id:
        raise HTTPException(status_code=400, detail="case_id required")
    res = agent.run_investigation(case_id, instruction)
    return res
