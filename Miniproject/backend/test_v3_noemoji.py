#!/usr/bin/env python
"""Quick test of agent_v3 endpoint - no emojis for Windows compatibility"""
import json
from app.api.v1 import agent_run_v3

payload = {"case_id": "test_case_001", "crime_type": "homicide"}
print("[*] Testing agent_run_v3 endpoint...")
print(f"Payload: {json.dumps(payload)}\n")

try:
    result = agent_run_v3(payload)
    print("[+] Endpoint executed successfully!")
    print(f"\n[RESULT SUMMARY]")
    print(f"  Case ID: {result.get('case_id')}")
    print(f"  Crime Type: {result.get('crime_type')}")
    print(f"  Timestamp: {result.get('timestamp')}")
    print(f"  Template: {result.get('template_name', 'N/A')}")
    stages = list(result.get('stages', {}).keys())
    print(f"  Stages: {stages}")
    
    if result.get('error'):
        print(f"  [WARNING] Error: {result.get('error')[:100]}...")
    else:
        print(f"  [+] No errors - Investigation successful!")
        if result.get('evidence_citations'):
            print(f"  Evidence Citations: {len(result.get('evidence_citations', {}))} items")
    
    print(f"\n[FULL RESPONSE]")
    print(json.dumps(result, indent=2, default=str)[:2000])
    if len(json.dumps(result, default=str)) > 2000:
        print("... (truncated)")
    
except Exception as e:
    print(f"[-] Error: {e}")
    import traceback
    traceback.print_exc()
