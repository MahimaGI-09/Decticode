# backend/app/core/agent.py
import os
from typing import List, Dict, Any
from dotenv import load_dotenv
from datetime import datetime
import openai
import json

BASE = os.path.dirname(os.path.dirname(__file__))
load_dotenv(os.path.join(BASE, "..", "..", ".env"))

MODEL_PROVIDER = os.getenv("MODEL_PROVIDER", "openai")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# Lazy imports to avoid blocking on MongoDB
storage = None
embeddings = None
rag = None

def get_storage():
    global storage
    if storage is None:
        from . import storage as storage_module
        storage = storage_module
    return storage

def get_rag():
    global rag
    if rag is None:
        from . import rag as rag_module
        rag = rag_module
    return rag

if MODEL_PROVIDER == "openai":
    openai.api_key = OPENAI_API_KEY


# ---------- Agent config ----------
TOP_K = 5
SYSTEM_INSTRUCTION = (
    "You are the Investigator Assistant. Use ONLY the provided evidence excerpts. "
    "Do NOT invent facts. If something is not present in the evidence say 'Cannot confirm'. "
    "Always return JSON with fields: timeline (list), suspects (list of {name,score,reason,sources}), "
    "summary (short), and raw_logs (optional). Each entry in timeline must include timestamp, evidence_ids."
)

# ---------- Helper: convert retrieved docs to context ----------
def build_context_from_docs(docs: List[Dict[str, Any]]) -> str:
    parts = []
    for d in docs:
        excerpt = ""
        if d.get("ocr_text"):
            excerpt = d["ocr_text"][:1200]
        elif d.get("transcript"):
            excerpt = d["transcript"][:1200]
        else:
            excerpt = (d.get("text") or "")[:1200]
        parts.append(f"[{d.get('evidence_id') or d.get('_id')}] {excerpt}")
    return "\n\n".join(parts)

# ---------- OpenAI call (chat completion) ----------
def call_openai_chat(system_prompt: str, user_prompt: str, temperature: float = 0.0) -> Dict[str, Any]:
    resp = openai.ChatCompletion.create(
        model="gpt-4o-mini" if False else "gpt-4o-mini",  # replace with your preferred model available to you
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ],
        temperature=temperature,
        max_tokens=1200
    )
    return resp

# ---------- Gemini / Vertex placeholder ----------
def call_gemini_placeholder(system_prompt: str, user_prompt: str) -> Dict[str, Any]:
    # This is where you'd call Google Vertex AI / Gemini using their client libraries.
    # For now, raise NotImplementedError or return a stub that uses openai as fallback.
    raise NotImplementedError("Gemini provider not implemented in this prototype. Use OpenAI or add your Vertex call here.")

# ---------- Main agent entry point ----------
def run_investigation(case_id: str, question: str = "Investigate and provide timeline and suspect list.") -> Dict[str, Any]:
    start = datetime.utcnow().isoformat()
    
    # If mock provider, return safe dummy response
    if MODEL_PROVIDER == "mock":
        mock_response = {
            "case_id": case_id,
            "retrieved_count": 0,
            "raw_model_text": "Mock response - no AI provider configured",
            "result": {
                "timeline": [
                    {"timestamp": "2025-12-06T10:00:00Z", "event": "Case opened", "evidence_ids": []}
                ],
                "suspects": [
                    {"name": "Unknown Suspect", "score": 0, "reason": "Insufficient evidence", "sources": []}
                ],
                "summary": "Case summary unavailable - agent provider not configured"
            },
            "run_id": None
        }
        return mock_response
    
    try:
        # 1) Retrieve top-K docs using your existing RAG / retrieval function
        # Assumes rag.retrieve_topk returns list of evidence docs (metadata + text)
        rag_module = get_rag()
        retrieved_docs = rag_module.retrieve_for_case(case_id, query=question, top_k=TOP_K)

        context = build_context_from_docs(retrieved_docs)

        # 2) Build user prompt (structured)
        user_prompt = (
            f"CONTEXT:\n{context}\n\n"
            f"INSTRUCTION:\n{question}\n\n"
            "Return valid JSON only containing fields: timeline, suspects, summary, raw_logs(optional). "
            "Timeline entries should have fields: {timestamp, event, evidence_ids}. "
            "Suspects should be array of {name,score (0-100),reason,sources:[evidence_id]}. "
            "If data is missing, state 'Cannot confirm'."
        )

        # 3) Call model based on provider
        if MODEL_PROVIDER == "openai":
            resp = call_openai_chat(SYSTEM_INSTRUCTION, user_prompt, temperature=0.0)
            text = resp["choices"][0]["message"]["content"]
        else:
            # For now fallback or raise
            try:
                text = call_gemini_placeholder(SYSTEM_INSTRUCTION, user_prompt)
            except Exception as e:
                return {"error": "No model provider available", "detail": str(e)}

        # 4) Try to parse JSON from model safely
        parsed = None
        try:
            # models sometimes wrap JSON in backticks; attempt to extract JSON
            start_idx = text.find("{")
            end_idx = text.rfind("}")
            if start_idx != -1 and end_idx != -1:
                json_str = text[start_idx:end_idx+1]
                parsed = json.loads(json_str)
            else:
                parsed = {"raw_text": text}
        except Exception as e:
            parsed = {"raw_text": text, "parse_error": str(e)}

        # 5) Save a run log to DB
        storage_module = get_storage()
        run_log = {
            "case_id": case_id,
            "question": question,
            "retrieved_ids": [d.get("evidence_id") or d.get("_id") for d in retrieved_docs],
            "model_output": text,
            "parsed_output": parsed,
            "start": start,
            "end": datetime.utcnow().isoformat()
        }
        storage_module.get_db()["agent_runs"].insert_one(run_log)

        # 6) Return parsed results plus metadata
        return {
            "case_id": case_id,
            "retrieved_count": len(retrieved_docs),
            "raw_model_text": text,
            "result": parsed,
            "run_id": str(run_log.get("_id", "")) if run_log.get("_id") else None
        }
    except Exception as e:
        # Fallback for any errors (including DB connection issues)
        return {
            "case_id": case_id,
            "error": str(e),
            "result": {
                "timeline": [],
                "suspects": [],
                "summary": f"Error during investigation: {str(e)}"
            }
        }
