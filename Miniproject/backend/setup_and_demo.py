#!/usr/bin/env python
"""
Setup script: Creates test case data and runs a full investigation
"""
import json
from app.core import storage, agent_v3

print("=" * 70)
print("STEP AGENT 3 - FULL SETUP & DEMONSTRATION")
print("=" * 70)

# Step 1: Create test case
print("\n[STEP 1] Creating test case...")
try:
    db = storage.get_db()
    
    case_data = {
        "case_id": "homicide_2024_001",
        "title": "The Riverside Murder",
        "description": "Victim found at Riverside Park with knife wound. Multiple suspects identified.",
        "status": "active",
        "created_at": "2024-01-15"
    }
    
    db["cases"].update_one(
        {"case_id": case_data["case_id"]},
        {"$set": case_data},
        upsert=True
    )
    print(f"  ✓ Case created: {case_data['case_id']}")
    print(f"    Title: {case_data['title']}")
except Exception as e:
    print(f"  ⚠ Could not create case (DB may be offline): {str(e)[:100]}")

# Step 2: Add evidence
print("\n[STEP 2] Adding evidence...")
evidence_items = [
    {
        "case_id": "homicide_2024_001",
        "type": "text",
        "description": "Witness Statement - Sarah Chen",
        "content": "I saw a man in a dark jacket running from the park around 9:15 PM. He had a knife in his hand. I recognized him - it was John from the office.",
        "timestamp": "2024-01-15T21:30:00"
    },
    {
        "case_id": "homicide_2024_001",
        "type": "text",
        "description": "Witness Statement - Park Security",
        "content": "Security camera footage shows three individuals near the crime scene between 9:00 PM and 9:30 PM. One matches the suspect's description.",
        "timestamp": "2024-01-15T21:45:00"
    },
    {
        "case_id": "homicide_2024_001",
        "type": "physical",
        "description": "Murder Weapon",
        "content": "Kitchen knife recovered from trash can 100 meters from crime scene. Fingerprints match John Smith.",
        "timestamp": "2024-01-15T22:00:00"
    },
    {
        "case_id": "homicide_2024_001",
        "type": "text",
        "description": "Victim Profile",
        "content": "Victim: Robert Harrison, 42, worked at Harrison & Co. Had financial disputes with employee John Smith over missing funds.",
        "timestamp": "2024-01-15T20:00:00"
    },
    {
        "case_id": "homicide_2024_001",
        "type": "text",
        "description": "Suspect Information",
        "content": "John Smith, 38, worked under Robert Harrison. Had motive (embezzlement cover-up). Opportunity (was at park that evening). Means (had access to kitchen knife from office).",
        "timestamp": "2024-01-15T23:00:00"
    },
    {
        "case_id": "homicide_2024_001",
        "type": "log",
        "description": "Timeline",
        "content": "8:45 PM - Victim last seen leaving office. 9:00 PM - Security camera shows three people at park. 9:15 PM - Witness reports seeing man with knife. 9:30 PM - Body discovered.",
        "timestamp": "2024-01-15T23:30:00"
    }
]

try:
    for evidence in evidence_items:
        storage.insert_evidence(
            case_id=evidence["case_id"],
            evidence_type=evidence["type"],
            description=evidence["description"],
            content=evidence["content"]
        )
    print(f"  ✓ Added {len(evidence_items)} evidence items")
    for item in evidence_items:
        print(f"    - {item['description']}")
except Exception as e:
    print(f"  ⚠ Could not add evidence (DB may be offline): {str(e)[:100]}")

# Step 3: Run investigation
print("\n[STEP 3] Running STEP AGENT 3 Investigation...")
print("  Template: Homicide Investigation")
print("  LLM Provider: openai (with mock fallback)")
print("  Search Mode: Semantic + Keyword Hybrid")
print("")

try:
    result = agent_v3.run_investigation_v3(
        case_id="homicide_2024_001",
        crime_type="homicide",
        use_semantic_search=True,
        hybrid_weight=0.7,
        max_evidence=6,
        llm_provider="mock"  # Using mock for demo to avoid API calls
    )
    
    print("  ✓ Investigation completed!")
    print(f"    Case ID: {result.get('case_id')}")
    print(f"    Crime Type: {result.get('crime_type')}")
    print(f"    Template: {result.get('template_name')}")
    print(f"    Timestamp: {result.get('timestamp')}")
    print(f"    LLM Provider: {result.get('llm_provider')}")
    
    # Show stages
    stages = result.get('stages', {})
    if stages:
        print(f"    Stages Completed: {len(stages)}")
        for stage_name, stage_data in stages.items():
            status = stage_data.get('status', 'unknown')
            print(f"      ✓ {stage_name}: {status}")
    
    if result.get('error'):
        print(f"    Note: {result.get('error')[:80]}...")
    else:
        print(f"    Status: SUCCESS")
    
    # Step 4: Show results
    print("\n[STEP 4] Investigation Results")
    print("-" * 70)
    print("\nFull Investigation Output:")
    print(json.dumps(result, indent=2, default=str)[:3000])
    print("\n... (output truncated)")
    
except Exception as e:
    print(f"  Error during investigation: {e}")
    import traceback
    traceback.print_exc()

print("\n" + "=" * 70)
print("SETUP COMPLETE")
print("=" * 70)
print("\nYou can now:")
print("  1. Start the server: python -m uvicorn app.main:app --reload")
print("  2. Query the API: http://127.0.0.1:8000/api/v1/agent/run/v3")
print("  3. Check explainability: http://127.0.0.1:8000/api/v1/investigate/homicide_2024_001/explain")
print("  4. Search evidence: http://127.0.0.1:8000/api/v1/search/semantic")
print("\n" + "=" * 70)
