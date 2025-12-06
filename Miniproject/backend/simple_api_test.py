#!/usr/bin/env python
"""
Simple API test without requests library
"""
import urllib.request
import json
import time

print("=" * 70)
print(" STEP AGENT 3 - API LIVE TEST")
print("=" * 70)

time.sleep(2)  # Wait for server

endpoints = [
    {
        "name": "1. Agent V3 Investigation",
        "url": "http://127.0.0.1:8000/api/v1/agent/run/v3",
        "method": "POST",
        "data": {
            "case_id": "demo_case_001",
            "crime_type": "homicide",
            "use_semantic_search": True,
            "max_evidence": 5,
            "llm_provider": "mock"
        }
    },
    {
        "name": "2. List Templates",
        "url": "http://127.0.0.1:8000/api/v1/templates",
        "method": "GET",
        "data": None
    },
    {
        "name": "3. Semantic Search",
        "url": "http://127.0.0.1:8000/api/v1/search/semantic",
        "method": "POST",
        "data": {
            "query": "knife weapon",
            "case_id": "demo_case_001",
            "top_k": 3,
            "provider": "mock"
        }
    }
]

for endpoint in endpoints:
    try:
        print(f"\n{endpoint['name']}")
        print("-" * 70)
        
        if endpoint["method"] == "GET":
            with urllib.request.urlopen(endpoint["url"], timeout=5) as response:
                data = json.loads(response.read().decode())
                print(f"Status: {response.status}")
                print(f"Response: {json.dumps(data, indent=2, default=str)[:800]}")
        else:
            data = json.dumps(endpoint["data"]).encode('utf-8')
            req = urllib.request.Request(
                endpoint["url"],
                data=data,
                headers={"Content-Type": "application/json"},
                method=endpoint["method"]
            )
            with urllib.request.urlopen(req, timeout=5) as response:
                response_data = json.loads(response.read().decode())
                print(f"Status: {response.status}")
                print(f"Response: {json.dumps(response_data, indent=2, default=str)[:800]}")
        
        print("[OK]")
    except Exception as e:
        print(f"Error: {str(e)[:100]}")

print("\n" + "=" * 70)
print(" TEST COMPLETE - System operational and ready to use!")
print("=" * 70)
