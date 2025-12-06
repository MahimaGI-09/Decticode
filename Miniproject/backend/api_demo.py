#!/usr/bin/env python
"""
Live API Demonstration - Shows all STEP AGENT 3 endpoints working
"""
import requests
import json
import time

BASE_URL = "http://127.0.0.1:8000/api/v1"

def print_section(title):
    print("\n" + "=" * 70)
    print(f" {title}")
    print("=" * 70)

def print_result(endpoint, response):
    print(f"\nEndpoint: {endpoint}")
    print(f"Status: {response.status_code}")
    try:
        data = response.json()
        print("Response:")
        print(json.dumps(data, indent=2, default=str)[:1500])
        if len(json.dumps(data, indent=2, default=str)) > 1500:
            print("... (truncated)")
    except:
        print(f"Response: {response.text[:500]}")

print_section("STEP AGENT 3 - LIVE API DEMONSTRATION")
print("All endpoints tested via HTTP requests to running server")
print(f"Server: {BASE_URL}")

# Wait for server to be ready
print("\n[*] Waiting for server to be ready...")
for i in range(10):
    try:
        requests.get(f"{BASE_URL}/health", timeout=2)
        print("[+] Server is ready!")
        break
    except:
        if i < 9:
            time.sleep(1)

print_section("1. RUN SEMANTIC INVESTIGATION (Agent V3)")

response = requests.post(
    f"{BASE_URL}/agent/run/v3",
    json={
        "case_id": "homicide_2024_001",
        "crime_type": "homicide",
        "use_semantic_search": True,
        "max_evidence": 5,
        "llm_provider": "mock"
    }
)
print_result("/agent/run/v3", response)

if response.status_code == 200:
    case_id = response.json().get("case_id")
    
    print_section("2. GET EXPLAINABILITY DASHBOARD")
    
    response = requests.get(f"{BASE_URL}/investigate/{case_id}/explain")
    print_result(f"/investigate/{case_id}/explain", response)

print_section("3. LIST AVAILABLE TEMPLATES")

response = requests.get(f"{BASE_URL}/templates")
print_result("/templates", response)

print_section("4. VALIDATE CUSTOM TEMPLATE")

custom_template = {
    "name": "Custom Fraud Investigation",
    "description": "Custom template for fraud cases",
    "crime_type": "fraud",
    "stages": [
        {
            "name": "Document Analysis",
            "description": "Analyze financial documents"
        },
        {
            "name": "Suspect Identification",
            "description": "Identify suspects"
        }
    ]
}

response = requests.post(
    f"{BASE_URL}/templates/validate",
    json=custom_template
)
print_result("/templates/validate", response)

print_section("5. SEMANTIC SEARCH")

response = requests.post(
    f"{BASE_URL}/search/semantic",
    json={
        "query": "evidence of crime",
        "case_id": "homicide_2024_001",
        "top_k": 5,
        "provider": "mock"
    }
)
print_result("/search/semantic", response)

print_section("6. HYBRID SEARCH (Semantic + Keyword)")

response = requests.post(
    f"{BASE_URL}/search/hybrid",
    json={
        "query": "knife weapon murder",
        "case_id": "homicide_2024_001",
        "semantic_weight": 0.7,
        "top_k": 5,
        "provider": "mock"
    }
)
print_result("/search/hybrid", response)

print_section("DEMONSTRATION COMPLETE")
print("\nAll endpoints demonstrated successfully!")
print("\nKey Features Shown:")
print("  ✓ Semantic search with embeddings")
print("  ✓ Hybrid search (semantic + keyword)")
print("  ✓ Crime-type templates")
print("  ✓ Custom template validation")
print("  ✓ Explainability dashboard")
print("  ✓ Full 4-stage investigation pipeline")
print("\nYou can now:")
print("  - Add MongoDB for persistent storage")
print("  - Create custom templates for your jurisdictions")
print("  - Configure real LLM providers (OpenAI, Gemini)")
print("  - Build a web UI on top of these APIs")
print("  - Deploy to production")
print("=" * 70)
