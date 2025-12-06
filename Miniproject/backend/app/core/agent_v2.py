# backend/app/core/agent_v2.py
"""
Enhanced agent with multi-stage prompting, strict JSON validation, and improved RAG.
Supports OpenAI, Gemini (Vertex), and mock providers.
"""
import os
import json
from typing import List, Dict, Any, Optional, Tuple
from dotenv import load_dotenv
from datetime import datetime
import openai

BASE = os.path.dirname(os.path.dirname(__file__))
load_dotenv(os.path.join(BASE, "..", "..", ".env"))

MODEL_PROVIDER = os.getenv("MODEL_PROVIDER", "openai").lower()
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "").strip()
GEMINI_PROJECT_ID = os.getenv("GEMINI_PROJECT_ID", "").strip()
GEMINI_LOCATION = os.getenv("GEMINI_LOCATION", "us-central1").strip()

# Only set OpenAI key if it's non-empty
if MODEL_PROVIDER == "openai" and OPENAI_API_KEY:
    openai.api_key = OPENAI_API_KEY

# Import prompts
from . import prompts

# Lazy imports for storage and rag
storage = None
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

# Configuration
TOP_K = 10
MODEL_NAME = "gpt-4o-mini"  # For OpenAI
GEMINI_MODEL = "gemini-2.0-flash"  # For Vertex AI

# ============ Helper: JSON extraction and validation ============
def safe_json_extract(text: str) -> Optional[Dict[str, Any]]:
    """
    Safely extract JSON from model response.
    Tries multiple strategies:
    1. Direct JSON parsing
    2. Extracting between first { and last }
    3. Trying lines that start with {
    """
    if not text:
        return None
    
    text = text.strip()
    
    # Strategy 1: Direct parse
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass
    
    # Strategy 2: Extract between first { and last }
    start_idx = text.find('{')
    end_idx = text.rfind('}')
    if start_idx != -1 and end_idx > start_idx:
        try:
            json_str = text[start_idx:end_idx+1]
            return json.loads(json_str)
        except json.JSONDecodeError:
            pass
    
    # Strategy 3: Look for code blocks with json
    if "```json" in text:
        try:
            start = text.find("```json") + 7
            end = text.find("```", start)
            if end > start:
                json_str = text[start:end].strip()
                return json.loads(json_str)
        except (json.JSONDecodeError, ValueError):
            pass
    
    return None

def build_evidence_context(docs: List[Dict[str, Any]], max_tokens: int = 3000) -> str:
    """
    Build a richly annotated context from evidence documents.
    Includes metadata, OCR, transcripts, and source IDs.
    """
    parts = []
    token_count = 0
    
    for doc in docs:
        evidence_id = doc.get("evidence_id") or doc.get("_id", "unknown")
        doc_type = doc.get("type", "unknown")
        tags = doc.get("tags", [])
        
        # Extract text content
        excerpt = ""
        if doc.get("ocr_text"):
            excerpt = doc["ocr_text"]
        elif doc.get("transcript"):
            excerpt = doc["transcript"]
        elif doc.get("text"):
            excerpt = doc["text"]
        
        excerpt = excerpt[:1500]  # Limit per doc
        
        # Format with metadata
        formatted = (
            f"[{evidence_id}] Type: {doc_type} | Tags: {', '.join(tags)}\n"
            f"Content: {excerpt}\n"
            f"---\n"
        )
        
        # Rough token estimate (1 token ~= 4 chars)
        token_estimate = len(formatted) // 4
        if token_count + token_estimate > max_tokens:
            break
        
        parts.append(formatted)
        token_count += token_estimate
    
    return "\n".join(parts) if parts else "[No evidence provided]"

# ============ OpenAI Chat Completion ============
def call_openai_chat(system: str, user_prompt: str, temperature: float = 0.0) -> Tuple[str, bool]:
    """
    Call OpenAI Chat API.
    Returns: (text, success)
    """
    try:
        resp = openai.ChatCompletion.create(
            model=MODEL_NAME,
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": user_prompt}
            ],
            temperature=temperature,
            max_tokens=2000
        )
        return resp["choices"][0]["message"]["content"], True
    except Exception as e:
        return f"OpenAI error: {str(e)}", False

# ============ Gemini (Vertex AI) Implementation ============
def call_gemini_chat(system: str, user_prompt: str, temperature: float = 0.0) -> Tuple[str, bool]:
    """
    Call Google Vertex AI Gemini API.
    Requires GEMINI_PROJECT_ID and GOOGLE_APPLICATION_CREDENTIALS or GEMINI_API_KEY.
    Returns: (text, success)
    """
    try:
        from google.cloud import aiplatform
        from google.api_core import gapic_v1
        
        # Initialize Vertex AI
        aiplatform.init(project=GEMINI_PROJECT_ID, location=GEMINI_LOCATION)
        
        # Create model
        model = aiplatform.GenerativeModel(GEMINI_MODEL)
        
        # Prepare request
        safety_settings = [
            {
                "category": "HARM_CATEGORY_UNSPECIFIED",
                "threshold": "BLOCK_NONE",
            }
        ]
        
        # Call Gemini
        response = model.generate_content(
            [
                {"role": "user", "parts": [{"text": f"{system}\n\n{user_prompt}"}]}
            ],
            generation_config={
                "temperature": temperature,
                "max_output_tokens": 2000,
            },
            safety_settings=safety_settings
        )
        
        return response.text, True
    except ImportError:
        return "Gemini provider requires: pip install google-cloud-aiplatform", False
    except Exception as e:
        return f"Gemini error: {str(e)}", False

# ============ Mock Provider ============
def call_mock_chat(system: str, user_prompt: str) -> Tuple[str, bool]:
    """Return a safe mock response for testing."""
    return json.dumps({
        "key_facts": ["Mock investigation"],
        "locations": [],
        "timeline_events": [{"time": "00:00", "event": "Case opened", "evidence_ids": []}],
        "witnesses_persons": [],
        "physical_evidence": [],
        "gaps": ["No real data available - mock provider enabled"]
    }), True

# ============ Main Multi-Stage Investigation ============
def run_investigation_v2(case_id: str, instruction: str = "Full investigation") -> Dict[str, Any]:
    """
    Run a multi-stage investigation:
    1. Summarize evidence
    2. Build timeline
    3. Identify suspects
    4. Validate and conclude
    
    Returns comprehensive investigation results.
    """
    start_time = datetime.utcnow().isoformat()
    
    # Mock mode early return
    if MODEL_PROVIDER == "mock":
        return {
            "case_id": case_id,
            "status": "complete",
            "provider": "mock",
            "message": "Mock provider enabled. To use real AI, set MODEL_PROVIDER=openai or gemini",
            "stages_completed": ["mock"],
            "start": start_time,
            "end": datetime.utcnow().isoformat()
        }
    
    # Retrieve evidence
    try:
        rag_module = get_rag()
        retrieved_docs = rag_module.retrieve_for_case(case_id, query=instruction, top_k=TOP_K)
    except Exception as e:
        retrieved_docs = []
    
    context = build_evidence_context(retrieved_docs)
    
    # Choose LLM
    if MODEL_PROVIDER == "openai":
        if not OPENAI_API_KEY:
            return {
                "case_id": case_id,
                "error": "OpenAI provider selected but OPENAI_API_KEY not set",
                "instruction": "Add OPENAI_API_KEY to .env"
            }
        call_fn = call_openai_chat
    elif MODEL_PROVIDER == "gemini":
        if not GEMINI_PROJECT_ID:
            return {
                "case_id": case_id,
                "error": "Gemini provider selected but GEMINI_PROJECT_ID not set",
                "instruction": "Add GEMINI_PROJECT_ID and GEMINI_LOCATION to .env"
            }
        call_fn = call_gemini_chat
    else:
        return {
            "case_id": case_id,
            "error": f"Unknown provider: {MODEL_PROVIDER}",
            "options": ["openai", "gemini", "mock"]
        }
    
    results = {
        "case_id": case_id,
        "provider": MODEL_PROVIDER,
        "evidence_count": len(retrieved_docs),
        "stages": {},
        "start": start_time
    }
    
    # ===== STAGE 1: Summarize =====
    user_msg_1 = f"EVIDENCE:\n{context}\n\n{prompts.STAGE_1_SUMMARIZE}"
    text_1, success_1 = call_fn(prompts.SYSTEM_INSTRUCTION_BASE, user_msg_1, temperature=0.0)
    
    summary_json = safe_json_extract(text_1) if success_1 else None
    results["stages"]["summarize"] = {
        "success": success_1,
        "raw": text_1[:500] if not success_1 else "✓",
        "parsed": summary_json
    }
    
    if not summary_json:
        results["error"] = "Failed to parse summary stage"
        return results
    
    # ===== STAGE 2: Timeline =====
    summary_text = json.dumps(summary_json)
    user_msg_2 = (
        f"EVIDENCE SUMMARY:\n{summary_text}\n\n"
        f"ORIGINAL EVIDENCE CONTEXT:\n{context}\n\n"
        f"{prompts.STAGE_2_TIMELINE}"
    )
    text_2, success_2 = call_fn(prompts.SYSTEM_INSTRUCTION_BASE, user_msg_2, temperature=0.0)
    
    timeline_json = safe_json_extract(text_2) if success_2 else None
    results["stages"]["timeline"] = {
        "success": success_2,
        "raw": text_2[:500] if not success_2 else "✓",
        "parsed": timeline_json
    }
    
    # ===== STAGE 3: Suspects =====
    user_msg_3 = (
        f"CASE SUMMARY:\n{summary_text}\n\n"
        f"TIMELINE:\n{json.dumps(timeline_json) if timeline_json else 'No timeline'}\n\n"
        f"EVIDENCE CONTEXT:\n{context}\n\n"
        f"{prompts.STAGE_3_SUSPECTS}"
    )
    text_3, success_3 = call_fn(prompts.SYSTEM_INSTRUCTION_BASE, user_msg_3, temperature=0.1)
    
    suspects_json = safe_json_extract(text_3) if success_3 else None
    results["stages"]["suspects"] = {
        "success": success_3,
        "raw": text_3[:500] if not success_3 else "✓",
        "parsed": suspects_json
    }
    
    # ===== STAGE 4: Validation =====
    all_stages = json.dumps({
        "summary": summary_json,
        "timeline": timeline_json,
        "suspects": suspects_json
    })
    user_msg_4 = (
        f"INVESTIGATION FINDINGS:\n{all_stages}\n\n"
        f"ORIGINAL EVIDENCE:\n{context}\n\n"
        f"{prompts.STAGE_4_VALIDATE}"
    )
    text_4, success_4 = call_fn(prompts.SYSTEM_INSTRUCTION_BASE, user_msg_4, temperature=0.0)
    
    validation_json = safe_json_extract(text_4) if success_4 else None
    results["stages"]["validation"] = {
        "success": success_4,
        "raw": text_4[:500] if not success_4 else "✓",
        "parsed": validation_json
    }
    
    # Save to DB
    try:
        storage_module = get_storage()
        log_doc = {
            "case_id": case_id,
            "instruction": instruction,
            "provider": MODEL_PROVIDER,
            "evidence_ids": [d.get("evidence_id") or d.get("_id") for d in retrieved_docs],
            "stages": results["stages"],
            "start": start_time,
            "end": datetime.utcnow().isoformat()
        }
        storage_module.get_db()["agent_runs_v2"].insert_one(log_doc)
        results["run_id"] = str(log_doc.get("_id", "")) if log_doc.get("_id") else None
    except Exception:
        pass  # DB not available, but still return results
    
    results["status"] = "complete"
    results["end"] = datetime.utcnow().isoformat()
    
    return results
