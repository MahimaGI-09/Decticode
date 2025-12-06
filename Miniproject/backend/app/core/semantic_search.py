# backend/app/core/semantic_search.py
"""
Semantic search module using embeddings for evidence retrieval.
Supports hybrid search (keyword + semantic) and vector DB operations.
"""
from typing import List, Dict, Any, Optional, Tuple
from . import embeddings_v2, storage

def build_evidence_embeddings(case_id: str) -> Dict[str, List[float]]:
    """
    Build and cache embeddings for all evidence in a case.
    Stores embeddings in MongoDB for later retrieval.
    
    Returns:
        Dict mapping evidence_id to embedding vector
    """
    docs = storage.list_evidence_by_case(case_id, limit=100)
    embeddings_dict = {}
    
    for doc in docs:
        evidence_id = doc.get("evidence_id") or doc.get("_id")
        
        # Build searchable text from all fields
        text_parts = [
            doc.get("ocr_text", ""),
            doc.get("transcript", ""),
            doc.get("text", ""),
            " ".join(doc.get("tags", [])),
        ]
        combined_text = " ".join([str(p) for p in text_parts if p])
        
        if not combined_text.strip():
            continue
        
        # Embed
        embedding = embeddings_v2.embed_text(combined_text)
        
        if embedding:
            embeddings_dict[evidence_id] = embedding
            
            # Store in MongoDB for persistence
            try:
                storage.get_db()["evidence_embeddings"].update_one(
                    {"evidence_id": evidence_id},
                    {
                        "$set": {
                            "evidence_id": evidence_id,
                            "case_id": case_id,
                            "embedding": embedding,
                            "embedding_provider": embeddings_v2.EMBEDDING_PROVIDER,
                            "indexed_at": storage.datetime.utcnow()
                        }
                    },
                    upsert=True
                )
            except Exception:
                pass  # DB not available, continue with memory cache
    
    return embeddings_dict

def semantic_search(
    case_id: str,
    query: str,
    top_k: int = 10,
    use_cache: bool = True
) -> List[Dict[str, Any]]:
    """
    Search for evidence using semantic similarity.
    
    Strategy:
    1. Embed the query
    2. Retrieve cached evidence embeddings (or build if needed)
    3. Compute similarity scores
    4. Return top_k by relevance with confidence scores
    
    Args:
        case_id: Case to search
        query: Natural language query
        top_k: Number of results to return
        use_cache: Use stored embeddings from DB
    
    Returns:
        List of evidence docs sorted by semantic similarity
    """
    # Embed query
    query_embedding = embeddings_v2.embed_text(query)
    if not query_embedding:
        # Fallback to keyword search if embedding fails
        return semantic_search_fallback(case_id, query, top_k)
    
    # Get evidence embeddings (from cache or rebuild)
    if use_cache:
        embeddings_list = []
        evidence_by_id = {}
        
        try:
            cached = storage.get_db()["evidence_embeddings"].find({"case_id": case_id})
            for doc in cached:
                evidence_id = doc.get("evidence_id")
                embedding = doc.get("embedding")
                if evidence_id and embedding:
                    embeddings_list.append((evidence_id, embedding))
                    evidence_by_id[evidence_id] = doc
        except Exception:
            # DB not available, build in memory
            pass
        
        if not embeddings_list:
            # Build embeddings in memory if cache miss
            embeddings_dict = build_evidence_embeddings(case_id)
            embeddings_list = [(eid, emb) for eid, emb in embeddings_dict.items()]
    else:
        # Build fresh embeddings
        embeddings_dict = build_evidence_embeddings(case_id)
        embeddings_list = [(eid, emb) for eid, emb in embeddings_dict.items()]
    
    if not embeddings_list:
        return []
    
    # Compute similarities
    similarities = []
    for evidence_id, emb in embeddings_list:
        sim = embeddings_v2.similarity(query_embedding, emb)
        similarities.append((evidence_id, sim))
    
    # Sort by similarity
    similarities.sort(key=lambda x: x[1], reverse=True)
    
    # Fetch full documents
    results = []
    for evidence_id, sim_score in similarities[:top_k]:
        doc = storage.get_evidence_by_id(str(evidence_id))
        if doc:
            doc["_semantic_similarity"] = sim_score
            doc["_similarity_confidence"] = int(sim_score * 100) if 0 <= sim_score <= 1 else 50
            results.append(doc)
    
    return results

def semantic_search_fallback(case_id: str, query: str, top_k: int = 10) -> List[Dict[str, Any]]:
    """
    Fallback keyword-based search when embeddings unavailable.
    Uses tag matching and text search.
    """
    from . import rag
    results = rag.retrieve_for_case(case_id, query=query, top_k=top_k)
    
    # Add mock confidence scores
    for r in results:
        r["_semantic_similarity"] = 0.5
        r["_similarity_confidence"] = 50
        r["_note"] = "Keyword search (embeddings unavailable)"
    
    return results

def hybrid_search(
    case_id: str,
    query: str,
    top_k: int = 10,
    semantic_weight: float = 0.7,
    keyword_weight: float = 0.3
) -> List[Dict[str, Any]]:
    """
    Combine semantic and keyword search with configurable weights.
    
    Args:
        case_id: Case to search
        query: Search query
        top_k: Results to return
        semantic_weight: Weight for semantic similarity (0-1)
        keyword_weight: Weight for keyword relevance (0-1)
    
    Returns:
        Ranked list of evidence combining both signals
    """
    # Semantic search
    semantic_results = semantic_search(case_id, query, top_k=top_k*2)
    
    # Keyword search
    from . import rag
    keyword_results = rag.retrieve_for_case(case_id, query=query, top_k=top_k*2)
    
    # Merge and rank by combined score
    combined = {}
    
    for doc in semantic_results:
        doc_id = doc.get("_id") or doc.get("evidence_id")
        sim = doc.get("_semantic_similarity", 0.5)
        combined[doc_id] = {
            "doc": doc,
            "semantic_score": sim,
            "keyword_score": 0.0
        }
    
    for doc in keyword_results:
        doc_id = doc.get("_id") or doc.get("evidence_id")
        keyword_score = doc.get("_relevance_score", 5) / 10.0  # Normalize to 0-1
        
        if doc_id in combined:
            combined[doc_id]["keyword_score"] = keyword_score
        else:
            combined[doc_id] = {
                "doc": doc,
                "semantic_score": 0.0,
                "keyword_score": keyword_score
            }
    
    # Compute hybrid score
    for doc_id in combined:
        sem = combined[doc_id]["semantic_score"]
        kw = combined[doc_id]["keyword_score"]
        combined[doc_id]["hybrid_score"] = (sem * semantic_weight) + (kw * keyword_weight)
    
    # Sort and return
    sorted_items = sorted(combined.items(), key=lambda x: x[1]["hybrid_score"], reverse=True)
    
    results = []
    for doc_id, scores in sorted_items[:top_k]:
        doc = scores["doc"]
        doc["_hybrid_score"] = scores["hybrid_score"]
        doc["_semantic_component"] = scores["semantic_score"]
        doc["_keyword_component"] = scores["keyword_score"]
        results.append(doc)
    
    return results
