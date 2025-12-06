# backend/app/api/attach_agent.py
from app.api.v1 import router as v1_router
from fastapi import HTTPException
from app.core import agent

@v1_router.post("/agent/run")
def agent_run(payload: dict):
    case_id = payload.get("case_id")
    instruction = payload.get("instruction", "Investigate and provide timeline and suspects.")
    if not case_id:
        raise HTTPException(status_code=400, detail="case_id required")
    res = agent.run_investigation(case_id, instruction)
    return res
