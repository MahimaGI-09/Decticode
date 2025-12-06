# backend/app/core/embeddings_v2.py
"""
Enhanced embeddings module with support for multiple providers:
- OpenAI text-embedding-3-small
- Google Vertex AI embeddings
- Sentence-transformers (local, no API needed)
- Mock embeddings (for testing)
"""
import os
from typing import List, Optional
import numpy as np
from dotenv import load_dotenv

BASE = os.path.dirname(os.path.dirname(__file__))
load_dotenv(os.path.join(BASE, "..", "..", ".env"))

EMBEDDING_PROVIDER = os.getenv("EMBEDDING_PROVIDER", "mock").lower()
EMBEDDING_DIM = 1536  # Default for OpenAI; will vary by provider

# ============ OpenAI Embeddings ============
def get_openai_embedding(text: str) -> Optional[List[float]]:
    """Get embedding from OpenAI."""
    try:
        import openai
        api_key = os.getenv("OPENAI_API_KEY", "").strip()
        if not api_key:
            return None
        
        response = openai.Embedding.create(
            input=text[:8000],  # Truncate to avoid token limits
            model="text-embedding-3-small"
        )
        return response["data"][0]["embedding"]
    except Exception as e:
        print(f"OpenAI embedding error: {e}")
        return None

# ============ Sentence-Transformers (Local) ============
_st_model = None

def get_local_embedding(text: str) -> Optional[List[float]]:
    """Get embedding using sentence-transformers (local, no API)."""
    try:
        global _st_model
        if _st_model is None:
            from sentence_transformers import SentenceTransformer
            # Use a small model for speed
            _st_model = SentenceTransformer('all-MiniLM-L6-v2')
        
        embedding = _st_model.encode(text, convert_to_tensor=False)
        return embedding.tolist() if hasattr(embedding, 'tolist') else list(embedding)
    except ImportError:
        print("sentence-transformers not installed. Install with: pip install sentence-transformers")
        return None
    except Exception as e:
        print(f"Local embedding error: {e}")
        return None

# ============ Google Vertex AI Embeddings ============
def get_gemini_embedding(text: str) -> Optional[List[float]]:
    """Get embedding from Google Vertex AI."""
    try:
        from google.cloud import aiplatform
        
        project_id = os.getenv("GEMINI_PROJECT_ID", "").strip()
        location = os.getenv("GEMINI_LOCATION", "us-central1").strip()
        
        if not project_id:
            return None
        
        aiplatform.init(project=project_id, location=location)
        
        from vertexai.language_models import TextEmbeddingModel
        model = TextEmbeddingModel.from_pretrained("textembedding-gecko@001")
        
        embedding = model.get_embeddings([text[:8000]])[0].values
        return list(embedding)
    except Exception as e:
        print(f"Gemini embedding error: {e}")
        return None

# ============ Mock Embeddings (for testing) ============
def get_mock_embedding(text: str) -> List[float]:
    """Generate a deterministic mock embedding."""
    # Simple hash-based mock: same text always gets same embedding
    hash_val = hash(text) % 1000000
    np.random.seed(hash_val)
    return np.random.randn(384).tolist()  # 384-dim mock vector

# ============ Main Embedding Function ============
def embed_text(text: str, provider: Optional[str] = None) -> Optional[List[float]]:
    """
    Embed text using configured provider.
    
    Args:
        text: Text to embed
        provider: Provider name (openai, gemini, local, mock). If None, uses EMBEDDING_PROVIDER env var.
    
    Returns:
        Embedding vector as list of floats, or None if failed
    """
    if not text or not isinstance(text, str):
        return None
    
    provider = provider or EMBEDDING_PROVIDER
    
    text = text.strip()
    if not text:
        return None
    
    provider = (provider or EMBEDDING_PROVIDER).lower()
    
    if provider == "openai":
        return get_openai_embedding(text)
    elif provider == "gemini":
        return get_gemini_embedding(text)
    elif provider == "local":
        return get_local_embedding(text)
    else:  # mock
        return get_mock_embedding(text)

def embed_batch(texts: List[str], provider: Optional[str] = None) -> List[Optional[List[float]]]:
    """Embed multiple texts."""
    return [embed_text(t, provider=provider) for t in texts]

def similarity(vec1: List[float], vec2: List[float]) -> float:
    """
    Compute cosine similarity between two embedding vectors.
    
    Returns:
        Similarity score between -1 and 1 (higher = more similar)
    """
    if not vec1 or not vec2:
        return 0.0
    
    arr1 = np.array(vec1)
    arr2 = np.array(vec2)
    
    norm1 = np.linalg.norm(arr1)
    norm2 = np.linalg.norm(arr2)
    
    if norm1 == 0 or norm2 == 0:
        return 0.0
    
    return float(np.dot(arr1, arr2) / (norm1 * norm2))

def find_similar(query_embedding: List[float], embeddings: List[List[float]], top_k: int = 5) -> List[int]:
    """
    Find indices of top_k most similar embeddings to query.
    
    Returns:
        List of indices sorted by similarity (highest first)
    """
    if not query_embedding or not embeddings:
        return []
    
    similarities = [similarity(query_embedding, emb) for emb in embeddings]
    
    # Sort by similarity descending
    sorted_indices = sorted(range(len(similarities)), key=lambda i: similarities[i], reverse=True)
    
    return sorted_indices[:top_k]
