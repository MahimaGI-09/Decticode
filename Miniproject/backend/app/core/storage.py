# backend/app/core/storage.py
import os
from typing import List, Optional, Dict, Any
from pymongo import MongoClient
from pymongo.collection import Collection
from pymongo.database import Database
from dotenv import load_dotenv
from bson.objectid import ObjectId
from datetime import datetime

# Load .env (try a few common locations so .env can live at project root or backend/)
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))  # points to backend/
# look in: backend/.env, project_root/.env, parent-of-backend (fallback)
possible_envs = [
    os.path.join(BASE_DIR, ".env"),
    os.path.join(BASE_DIR, "..", ".env"),
    os.path.join(BASE_DIR, "..", "..", ".env"),
]
for p in possible_envs:
    if os.path.exists(p):
        load_dotenv(p)
        break
else:
    # final fallback: try load_dotenv() with no args (will search CWD)
    load_dotenv()

MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017")
DB_NAME = os.getenv("DB_NAME", "detective_sim")

# Singleton Mongo client
_client: Optional[MongoClient] = None
_db: Optional[Database] = None

def get_client() -> MongoClient:
    global _client
    if _client is None:
        _client = MongoClient(MONGO_URI, serverSelectionTimeoutMS=2000, connectTimeoutMS=2000)
    return _client

def get_db() -> Database:
    global _db
    if _db is None:
        _db = get_client()[DB_NAME]
    return _db

# Collections
def cases_collection() -> Collection:
    return get_db()["cases"]

def evidence_collection() -> Collection:
    return get_db()["evidence"]

def vectors_collection() -> Collection:
    return get_db()["vectors"]

def query_logs_collection() -> Collection:
    return get_db()["query_logs"]

# Helper functions
def insert_case(case_data: Dict[str, Any]) -> str:
    case_data.setdefault("created_at", datetime.utcnow())
    res = cases_collection().insert_one(case_data)
    return str(res.inserted_id)

def insert_evidence(evidence_data: Dict[str, Any]) -> str:
    """evidence_data should include: case_id, type, path, ocr_text/transcript, tags, timestamp (optional)"""
    evidence_data.setdefault("created_at", datetime.utcnow())
    res = evidence_collection().insert_one(evidence_data)
    return str(res.inserted_id)

def get_evidence_by_id(evidence_id: str) -> Optional[Dict[str, Any]]:
    try:
        doc = evidence_collection().find_one({"_id": ObjectId(evidence_id)})
    except Exception:
        # maybe user passed a non-ObjectId id (our ingests use string uuid sometimes)
        doc = evidence_collection().find_one({"evidence_id": evidence_id})
    if doc:
        doc["_id"] = str(doc["_id"])
    return doc

def list_evidence_by_case(case_id: str, limit: int = 50, skip: int = 0) -> List[Dict[str, Any]]:
    cursor = evidence_collection().find({"case_id": case_id}).skip(skip).limit(limit).sort("created_at", -1)
    docs = []
    for d in cursor:
        d["_id"] = str(d["_id"])
        docs.append(d)
    return docs

def list_all_evidence(limit: int = 100) -> List[Dict[str, Any]]:
    cursor = evidence_collection().find().sort("created_at", -1).limit(limit)
    docs = []
    for d in cursor:
        d["_id"] = str(d["_id"])
        docs.append(d)
    return docs

def upsert_vector(evidence_id: str, vector: List[float]) -> None:
    """Store the embedding vector in a collection (optional: used as backup)."""
    vectors_collection().update_one(
        {"evidence_id": evidence_id},
        {"$set": {"embedding": vector, "updated_at": datetime.utcnow()}},
        upsert=True
    )

def get_vector_by_evidence_id(evidence_id: str) -> Optional[List[float]]:
    doc = vectors_collection().find_one({"evidence_id": evidence_id})
    return doc.get("embedding") if doc else None

def insert_query_log(query: str, returned_evidence_ids: List[str], answer: str, meta: Optional[Dict[str, Any]] = None) -> str:
    entry = {
        "query": query,
        "returned_evidence_ids": returned_evidence_ids,
        "answer": answer,
        "meta": meta or {},
        "timestamp": datetime.utcnow()
    }
    res = query_logs_collection().insert_one(entry)
    return str(res.inserted_id)

def fetch_query_logs(limit: int = 50) -> List[Dict[str, Any]]:
    cursor = query_logs_collection().find().sort("timestamp", -1).limit(limit)
    out = []
    for d in cursor:
        d["_id"] = str(d["_id"])
        out.append(d)
    return out

def insert_agent_run_v3(case_id: str, crime_type: Optional[str], results: Dict[str, Any], evidence_citations: Dict[str, Any]) -> str:
    """Store v3 agent investigation results with evidence citations."""
    entry = {
        "case_id": case_id,
        "crime_type": crime_type,
        "results": results,
        "evidence_citations": evidence_citations,
        "timestamp": datetime.utcnow(),
        "version": 3
    }
    res = get_db()["agent_runs_v3"].insert_one(entry)
    return str(res.inserted_id)

def fetch_agent_run_v3(case_id: str) -> Optional[Dict[str, Any]]:
    """Fetch latest v3 agent run for a case."""
    doc = get_db()["agent_runs_v3"].find_one({"case_id": case_id}, sort=[("timestamp", -1)])
    if doc:
        doc["_id"] = str(doc["_id"])
    return doc

