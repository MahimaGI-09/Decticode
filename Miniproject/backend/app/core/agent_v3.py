# backend/app/core/agent_v3.py
"""
Agent v3: Semantic-search powered investigation with template-based prompts.
Combines embeddings, semantic search, and crime-type specific templates.
Produces detailed explainability output with evidence citations.
"""
import os
import json
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime

def get_templates():
    """Lazy load templates module."""
    from . import templates
    return templates

def get_semantic_search():
    """Lazy load semantic_search module."""
    from . import semantic_search
    return semantic_search

def get_embeddings():
    """Lazy load embeddings_v2 module."""
    from . import embeddings_v2
    return embeddings_v2

def get_storage():
    """Lazy load storage module."""
    from . import storage
    return storage

def get_explainability():
    """Lazy load explainability module."""
    from . import explainability
    return explainability

def call_openai_chat(messages: List[Dict], temperature: float = 0.7) -> str:
    """Call OpenAI API with lazy import."""
    try:
        import openai
        client = openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=messages,
            temperature=temperature,
            max_tokens=2000
        )
        return response.choices[0].message.content
    except Exception as e:
        print(f"OpenAI error: {e}, falling back to mock")
        return call_mock_chat(messages)

def call_gemini_chat(messages: List[Dict], temperature: float = 0.7) -> str:
    """Call Gemini API with lazy import."""
    try:
        import vertexai
        from vertexai.generative_models import GenerativeModel
        
        project = os.getenv("GOOGLE_CLOUD_PROJECT")
        location = os.getenv("GOOGLE_CLOUD_LOCATION", "us-central1")
        
        vertexai.init(project=project, location=location)
        model = GenerativeModel("gemini-1.5-flash")
        
        # Convert format for Gemini
        prompt = ""
        for msg in messages:
            prompt += f"{msg['role']}: {msg['content']}\n\n"
        
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        print(f"Gemini error: {e}, falling back to mock")
        return call_mock_chat(messages)

def call_mock_chat(messages: List[Dict]) -> str:
    """Mock chat for testing."""
    import json
    return json.dumps({
        "status": "mock_response",
        "message": "This is a mock response for testing",
        "timestamp": datetime.utcnow().isoformat()
    })

def safe_json_extract(text: str) -> Optional[Dict]:
    """Extract JSON from LLM output with 4 fallback strategies."""
    strategies = [
        lambda t: json.loads(t),  # Direct parse
        lambda t: json.loads(t[t.find('{'):t.rfind('}')+1]),  # Bracket extraction
        lambda t: json.loads(t[t.find('['):t.rfind(']')+1]) if '[' in t else None,  # Array extraction
        lambda t: json.loads(t.split('```json')[1].split('```')[0]) if '```json' in t else None,  # Code block
    ]
    
    for strategy in strategies:
        try:
            return strategy(text)
        except:
            continue
    
    return None

def run_investigation_v3(
    case_id: str,
    crime_type: Optional[str] = None,
    custom_template: Optional[Dict] = None,
    use_semantic_search: bool = True,
    hybrid_weight: float = 0.7,
    max_evidence: int = 8,
    llm_provider: Optional[str] = None
) -> Dict[str, Any]:
    """
    Run investigation using semantic search and crime-type templates.
    
    Args:
        case_id: Case identifier
        crime_type: Type of crime (homicide, theft, etc.) for template selection
        custom_template: Override with custom template dict
        use_semantic_search: Use semantic+keyword hybrid search (vs keyword only)
        hybrid_weight: Weight for semantic component in hybrid (0-1)
        max_evidence: Maximum evidence items to include in context
        llm_provider: LLM provider (openai, gemini, mock)
    
    Returns:
        Investigation results with evidence citations and explainability
    """
    templates_mod = get_templates()
    semantic_search_mod = get_semantic_search()
    embeddings_mod = get_embeddings()
    storage_mod = get_storage()
    explainability_mod = get_explainability()
    
    llm_provider = llm_provider or os.getenv("LLM_PROVIDER", "openai")
    
    results = {
        "case_id": case_id,
        "timestamp": datetime.utcnow().isoformat(),
        "llm_provider": llm_provider,
        "crime_type": crime_type,
        "use_semantic_search": use_semantic_search,
        "stages": {},
        "error": None
    }
    
    try:
        # Load template
        template = templates_mod.get_template(crime_type or "generic", custom_template)
        results["template_name"] = template.name
        
        # Get case data
        db = storage_mod.get_db()
        case_doc = db["cases"].find_one({"case_id": case_id})
        if not case_doc:
            results["error"] = f"Case {case_id} not found"
            return results
        
        # Build evidence context using semantic or keyword search
        query = case_doc.get("description", "")
        
        if use_semantic_search:
            try:
                # Build embeddings if needed
                semantic_search_mod.build_evidence_embeddings(case_id)
                
                # Hybrid search for better relevance
                evidence_results = semantic_search_mod.hybrid_search(
                    case_id=case_id,
                    query=query,
                    top_k=max_evidence,
                    semantic_weight=hybrid_weight,
                    keyword_weight=1 - hybrid_weight
                )
            except Exception as e:
                print(f"Semantic search failed: {e}, falling back to keyword")
                evidence_results = semantic_search_mod.semantic_search_fallback(
                    case_id=case_id,
                    query=query,
                    top_k=max_evidence
                )
        else:
            # Keyword-only search
            evidence_results = semantic_search_mod.semantic_search_fallback(
                case_id=case_id,
                query=query,
                top_k=max_evidence
            )
        
        evidence_by_id = {}
        for evidence in evidence_results:
            evidence_by_id[str(evidence["_id"])] = evidence
        
        results["evidence_context"] = {
            "total_found": len(evidence_results),
            "evidence_ids": [str(e["_id"]) for e in evidence_results],
            "search_method": "semantic" if use_semantic_search else "keyword"
        }
        
        # Run through each stage of template
        evidence_citations = {}  # Track evidence usage per stage
        
        for stage_idx, stage_name in enumerate(["summarize", "timeline", "suspects", "validation"]):
            stage_config = template.stages.get(stage_name)
            if not stage_config:
                continue
            
            # Build evidence context (truncate to ~3000 tokens)
            evidence_context = _build_evidence_context(evidence_results, max_tokens=3000)
            
            # Get stage prompt from template
            system_prompt = stage_config.get("system", "")
            user_prompt = stage_config.get("user_prompt", "")
            
            # Format user prompt with case data
            formatted_user_prompt = user_prompt.format(
                case_description=case_doc.get("description", ""),
                evidence_context=evidence_context,
                case_id=case_id
            )
            
            # Call LLM
            messages = [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": formatted_user_prompt}
            ]
            
            if llm_provider == "gemini":
                response = call_gemini_chat(messages)
            else:
                response = call_openai_chat(messages)
            
            # Parse response
            parsed = safe_json_extract(response)
            
            # Extract evidence citations from this stage
            stage_citations = _extract_evidence_citations(
                parsed or {},
                evidence_by_id,
                stage_name
            )
            
            results["stages"][stage_name] = {
                "status": "completed",
                "raw_response": response[:500] if isinstance(response, str) else str(response)[:500],
                "parsed": parsed,
                "evidence_citations": stage_citations,
                "confidence": _estimate_stage_confidence(parsed, stage_name)
            }
            
            # Aggregate citations
            for evidence_id, claims in stage_citations.items():
                if evidence_id not in evidence_citations:
                    evidence_citations[evidence_id] = []
                evidence_citations[evidence_id].extend(claims)
        
        results["evidence_citations"] = evidence_citations
        
        # Generate explainability report
        try:
            dashboard = explainability_mod.ExplainabilityDashboard(case_id, results)
            results["explainability"] = dashboard.get_full_dashboard()
        except Exception as e:
            print(f"Explainability generation failed: {e}")
            results["explainability_error"] = str(e)
        
        # Store results
        try:
            storage_mod.insert_agent_run_v3(
                case_id=case_id,
                crime_type=crime_type,
                results=results,
                evidence_citations=evidence_citations
            )
        except Exception as e:
            print(f"Failed to store results: {e}")
        
    except Exception as e:
        results["error"] = str(e)
        print(f"Investigation error: {e}")
    
    return results

def _build_evidence_context(evidence_list: List[Dict], max_tokens: int = 3000) -> str:
    """Build evidence context with token counting."""
    context_parts = []
    token_count = 0
    
    for evidence in evidence_list:
        # Estimate tokens (rough: 4 chars = 1 token)
        evidence_text = f"ID: {evidence['_id']}\nType: {evidence.get('type', 'unknown')}\nContent: {evidence.get('description', evidence.get('content', ''))}\n\n"
        tokens = len(evidence_text) // 4
        
        if token_count + tokens > max_tokens:
            break
        
        context_parts.append(evidence_text)
        token_count += tokens
    
    return "".join(context_parts) if context_parts else "No evidence available."

def _extract_evidence_citations(
    parsed: Dict,
    evidence_by_id: Dict,
    stage_name: str
) -> Dict[str, List[str]]:
    """
    Extract which evidence items were cited in this stage's findings.
    Returns {evidence_id: [claims]}
    """
    citations = {}
    
    if not parsed:
        return citations
    
    # Stage-specific citation extraction
    if stage_name == "summarize":
        # Look for evidence IDs in key facts, gaps, etc.
        for fact in parsed.get("key_facts", []):
            for eid in evidence_by_id:
                if str(eid) in fact:
                    if eid not in citations:
                        citations[eid] = []
                    citations[eid].append(fact)
    
    elif stage_name == "timeline":
        # Extract from timeline events
        for event in parsed.get("timeline", []):
            event_text = json.dumps(event)
            for eid in evidence_by_id:
                if str(eid) in event_text:
                    if eid not in citations:
                        citations[eid] = []
                    citations[eid].append(event.get("event", "Timeline event"))
    
    elif stage_name == "suspects":
        # Extract from suspect profiles
        for suspect in parsed.get("suspects", []):
            for evidence_id in suspect.get("evidence_against", []):
                if str(evidence_id) in evidence_by_id:
                    if str(evidence_id) not in citations:
                        citations[str(evidence_id)] = []
                    citations[str(evidence_id)].append(f"Evidence against {suspect.get('name')}")
    
    elif stage_name == "validation":
        # Extract from validated facts
        for fact in parsed.get("validated_facts", []):
            for eid in evidence_by_id:
                if str(eid) in fact:
                    if eid not in citations:
                        citations[eid] = []
                    citations[eid].append(fact)
    
    return citations

def _estimate_stage_confidence(parsed: Optional[Dict], stage_name: str) -> float:
    """Estimate confidence for this stage (0-100)."""
    if not parsed:
        return 0
    
    if stage_name == "timeline":
        conf_scores = []
        for event in parsed.get("timeline", []):
            conf = event.get("confidence")
            if conf == "high":
                conf_scores.append(90)
            elif conf == "medium":
                conf_scores.append(70)
            else:
                conf_scores.append(40)
        return sum(conf_scores) / len(conf_scores) if conf_scores else 50
    
    elif stage_name == "suspects":
        scores = [s.get("confidence_score", 50) for s in parsed.get("suspects", [])]
        return sum(scores) / len(scores) if scores else 50
    
    elif stage_name == "validation":
        total_facts = len(parsed.get("validated_facts", [])) + len(parsed.get("uncertain_claims", []))
        validated = len(parsed.get("validated_facts", []))
        return (validated / total_facts * 100) if total_facts > 0 else 50
    
    return 75  # Default confidence for summarize
