#!/usr/bin/env python
"""Test the agent/v3 API endpoint"""
import urllib.request
import json
import sys

print("🔍 RUNNING SEMANTIC INVESTIGATION API")
print("")
print("📍 Endpoint: POST http://127.0.0.1:8000/api/v1/agent/run/v3")
print("📋 Payload:")
print('{')
print('  "case_id": "case_001",')
print('  "crime_type": "homicide"')
print('}')
print("")
print("🔄 Sending request...")
print("")

payload = {
    "case_id": "case_001",
    "crime_type": "homicide"
}

try:
    url = "http://127.0.0.1:8000/api/v1/agent/run/v3"
    data = json.dumps(payload).encode('utf-8')
    
    req = urllib.request.Request(
        url,
        data=data,
        headers={'Content-Type': 'application/json'}
    )
    
    with urllib.request.urlopen(req, timeout=30) as response:
        result = json.loads(response.read().decode('utf-8'))
    
    print("✅ SUCCESS!")
    print("")
    print("📊 RESPONSE SUMMARY:")
    print(f"  Case ID: {result.get('case_id')}")
    print(f"  Crime Type: {result.get('crime_type')}")
    print(f"  Template: {result.get('template_name')}")
    print(f"  Timestamp: {result.get('timestamp')}")
    print(f"  LLM Provider: {result.get('llm_provider')}")
    print(f"  Stages Completed: {len(result.get('stages', {}))}")
    
    if result.get('error'):
        err_msg = result.get('error')
        if len(err_msg) > 150:
            err_msg = err_msg[:150] + "..."
        print(f"  ⚠️  Error: {err_msg}")
    else:
        print(f"  ✅ No errors")
    
    print("")
    print("📄 FULL RESPONSE (JSON):")
    print(json.dumps(result, indent=2, default=str))
    
except urllib.error.URLError as e:
    print(f"❌ CONNECTION ERROR: {e}")
    print(f"   Is the server running on http://127.0.0.1:8000 ?")
    sys.exit(1)
except Exception as e:
    print(f"❌ ERROR: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

print("")
print("✅ Test complete!")
