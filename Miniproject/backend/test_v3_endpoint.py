#!/usr/bin/env python
"""Quick test of agent_v3 endpoint"""
import json
from app.api.v1 import agent_run_v3

payload = {"case_id": "test_case_001", "crime_type": "homicide"}
print("📋 Testing agent_run_v3 endpoint...")
print(f"Payload: {json.dumps(payload)}\n")

try:
    result = agent_run_v3(payload)
    print("✓ Endpoint executed successfully!")
    print(f"\n📊 Result Summary:")
    print(f"  Case ID: {result.get('case_id')}")
    print(f"  Crime Type: {result.get('crime_type')}")
    print(f"  Timestamp: {result.get('timestamp')}")
    print(f"  Template: {result.get('template_name', 'N/A')}")
    stages = list(result.get('stages', {}).keys())
    print(f"  Stages: {stages}")
    
    if result.get('error'):
        print(f"  ⚠️  Error: {result.get('error')}")
    else:
        print(f"\n✅ Investigation completed successfully!")
        if result.get('evidence_citations'):
            print(f"  Evidence Citations: {len(result.get('evidence_citations', {}))} evidence items used")
    
    print(f"\n📄 Full Response:")
    print(json.dumps(result, indent=2, default=str)[:1000] + "...")
    
except Exception as e:
    print(f"✗ Error: {e}")
    import traceback
    traceback.print_exc()
