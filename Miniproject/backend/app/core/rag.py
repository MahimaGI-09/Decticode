# backend/app/core/rag.py
"""
Retrieval-Augmented Generation (RAG) module for evidence lookup.
Handles filtering, sorting, and ranking of evidence documents.
"""
from typing import List, Dict, Any
from datetime import datetime
from . import storage

def retrieve_for_case(case_id: str, query: str = "", top_k: int = 10) -> List[Dict[str, Any]]:
    """
    Retrieve and rank evidence documents for a case.
    
    Strategy:
    1. Fetch all evidence for the case
    2. Sort by relevance (type priority, tags match, recency)
    3. Return top_k
    
    Args:
        case_id: Case identifier
        query: Search query (optional; used for basic tag matching)
        top_k: Number of documents to return
    
    Returns:
        List of evidence documents, sorted by relevance
    """
    # Fetch all evidence for this case
    docs = storage.list_evidence_by_case(case_id, limit=100)
    
    if not docs:
        return []
    
    # Normalize evidence_id field
    for d in docs:
        if not d.get("evidence_id"):
            d["evidence_id"] = d.get("_id")
    
    # Simple relevance scoring
    query_lower = query.lower()
    query_terms = set(query_lower.split())
    
    for doc in docs:
        score = 0
        
        # Type priority (audio/video/text ranked by perceived importance)
        type_priority = {
            "audio": 10,
            "video": 9,
            "transcript": 8,
            "text": 6,
            "image": 5,
            "physical": 7,
            "log": 4,
            "other": 1
        }
        doc_type = doc.get("type", "other").lower()
        score += type_priority.get(doc_type, 1)
        
        # Tag matching
        tags = [t.lower() for t in doc.get("tags", [])]
        tag_matches = len(set(tags) & query_terms)
        score += tag_matches * 5
        
        # Recency boost (newer is slightly better)
        if doc.get("created_at"):
            # Simple recency: recent docs get small boost
            score += 0.5
        
        # Text relevance (if query appears in content)
        text = f"{doc.get('ocr_text', '')} {doc.get('transcript', '')}".lower()
        if query_lower in text:
            score += 3
        
        doc["_relevance_score"] = score
    
    # Sort by relevance (descending), then by creation date (newest first)
    docs.sort(
        key=lambda d: (
            -d.get("_relevance_score", 0),
            -(datetime.fromisoformat(d.get("created_at", "2000-01-01T00:00:00")) if d.get("created_at") else datetime(2000, 1, 1)).timestamp()
        )
    )
    
    # Return top_k
    return docs[:top_k]

def retrieve_similar_evidence(evidence_id: str, top_k: int = 5) -> List[Dict[str, Any]]:
    """
    Find similar evidence to a given evidence ID (e.g., same tags, similar type).
    """
    evidence = storage.get_evidence_by_id(evidence_id)
    if not evidence:
        return []
    
    case_id = evidence.get("case_id")
    tags = set(evidence.get("tags", []))
    doc_type = evidence.get("type")
    
    # Build query from tags and type
    query = f"{doc_type} {' '.join(tags)}"
    
    # Retrieve and filter
    all_docs = retrieve_for_case(case_id, query=query, top_k=20)
    
    # Exclude the original doc and return top_k similar ones
    similar = [d for d in all_docs if d.get("_id") != evidence_id]
    return similar[:top_k]

