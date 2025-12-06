# backend/app/api/v1.py
from fastapi import APIRouter, HTTPException
from app.core import storage, agent, agent_v2, agent_v3, semantic_search, templates

router = APIRouter()

@router.get("/health/db")
def db_health():
    # Quick non-blocking health check (doesn't wait for DB)
    return {"status": "ok", "message": "Backend API running"}

@router.get("/evidence")
def list_evidence(limit: int = 50):
    try:
        docs = storage.list_all_evidence(limit=limit)
        return {"status": "ok", "count": len(docs), "data": docs}
    except Exception:
        # If DB unavailable, return empty set
        return {"status": "ok", "count": 0, "data": [], "note": "MongoDB not available"}

@router.post("/agent/run")
def agent_run(payload: dict):
    """Legacy agent endpoint (v1)."""
    case_id = payload.get("case_id")
    instruction = payload.get("instruction", "Investigate and provide timeline and suspects.")
    if not case_id:
        raise HTTPException(status_code=400, detail="case_id required")
    res = agent.run_investigation(case_id, instruction)
    return res

@router.post("/agent/run/v2")
def agent_run_v2(payload: dict):
    """Enhanced agent endpoint with multi-stage investigation."""
    case_id = payload.get("case_id")
    instruction = payload.get("instruction", "Full investigation: summarize, timeline, identify suspects, validate")
    if not case_id:
        raise HTTPException(status_code=400, detail="case_id required")
    res = agent_v2.run_investigation_v2(case_id, instruction)
    return res

@router.post("/agent/run/v3")
def agent_run_v3(payload: dict):
    """Semantic-search powered agent with crime-type templates."""
    case_id = payload.get("case_id")
    crime_type = payload.get("crime_type")
    custom_template = payload.get("custom_template")
    use_semantic_search = payload.get("use_semantic_search", True)
    hybrid_weight = payload.get("hybrid_weight", 0.7)
    max_evidence = payload.get("max_evidence", 8)
    llm_provider = payload.get("llm_provider")
    
    if not case_id:
        raise HTTPException(status_code=400, detail="case_id required")
    
    res = agent_v3.run_investigation_v3(
        case_id=case_id,
        crime_type=crime_type,
        custom_template=custom_template,
        use_semantic_search=use_semantic_search,
        hybrid_weight=hybrid_weight,
        max_evidence=max_evidence,
        llm_provider=llm_provider
    )
    return res

@router.post("/search/semantic")
def search_semantic(payload: dict):
    """Semantic search endpoint."""
    case_id = payload.get("case_id")
    query = payload.get("query")
    top_k = payload.get("top_k", 5)
    
    if not case_id or not query:
        raise HTTPException(status_code=400, detail="case_id and query required")
    
    try:
        results = semantic_search.semantic_search(
            case_id=case_id,
            query=query,
            top_k=top_k
        )
        return {"status": "ok", "count": len(results), "data": results}
    except Exception as e:
        return {"status": "error", "message": str(e), "count": 0, "data": []}

@router.post("/search/hybrid")
def search_hybrid(payload: dict):
    """Hybrid semantic+keyword search endpoint."""
    case_id = payload.get("case_id")
    query = payload.get("query")
    top_k = payload.get("top_k", 5)
    semantic_weight = payload.get("semantic_weight", 0.7)
    
    if not case_id or not query:
        raise HTTPException(status_code=400, detail="case_id and query required")
    
    try:
        results = semantic_search.hybrid_search(
            case_id=case_id,
            query=query,
            top_k=top_k,
            semantic_weight=semantic_weight,
            keyword_weight=1 - semantic_weight
        )
        return {"status": "ok", "count": len(results), "data": results}
    except Exception as e:
        return {"status": "error", "message": str(e), "count": 0, "data": []}

@router.get("/templates")
def list_templates():
    """List available investigation templates."""
    try:
        template_list = templates.list_available_templates()
        return {
            "status": "ok",
            "count": len(template_list),
            "templates": template_list
        }
    except Exception as e:
        return {"status": "error", "message": str(e), "templates": []}

@router.post("/templates/validate")
def validate_template(payload: dict):
    """Validate a custom template."""
    try:
        custom_template = payload.get("template")
        if not custom_template:
            raise HTTPException(status_code=400, detail="template required")
        
        # Try to instantiate template to validate
        template = templates.InvestigationTemplate(
            name=custom_template.get("name", "custom"),
            description=custom_template.get("description", ""),
            stages=custom_template.get("stages", {})
        )
        return {
            "status": "ok",
            "message": "Template valid",
            "template": {
                "name": template.name,
                "description": template.description,
                "stages": list(template.stages.keys())
            }
        }
    except Exception as e:
        return {"status": "error", "message": str(e)}

@router.get("/investigate/{case_id}/explain")
def get_explainability(case_id: str):
    """Get explainability dashboard for case investigation."""
    try:
        run_result = storage.fetch_agent_run_v3(case_id)
        if not run_result:
            raise HTTPException(status_code=404, detail=f"No v3 investigation found for case {case_id}")
        
        explainability_data = run_result.get("results", {}).get("explainability", {})
        return {
            "status": "ok",
            "case_id": case_id,
            "explainability": explainability_data
        }
    except HTTPException:
        raise
    except Exception as e:
        return {
            "status": "error",
            "message": str(e),
            "case_id": case_id
        }




