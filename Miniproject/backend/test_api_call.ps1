#!/usr/bin/env powershell
# Make API call and display results

Write-Host "🔍 RUNNING SEMANTIC INVESTIGATION API" -ForegroundColor Cyan
Write-Host ""
Write-Host "📍 Endpoint: POST http://127.0.0.1:8000/api/v1/agent/run/v3" -ForegroundColor Yellow
Write-Host "📋 Payload:" 
Write-Host '{' -ForegroundColor Gray
Write-Host '  "case_id": "case_001",' -ForegroundColor Gray
Write-Host '  "crime_type": "homicide"' -ForegroundColor Gray
Write-Host '}' -ForegroundColor Gray
Write-Host ""
Write-Host "🔄 Sending request..." -ForegroundColor Cyan

$json = '{"case_id": "case_001", "crime_type": "homicide"}'

try {
    $resp = Invoke-RestMethod -Uri "http://127.0.0.1:8000/api/v1/agent/run/v3" `
        -Method Post `
        -ContentType "application/json" `
        -Body $json `
        -TimeoutSec 30
    
    Write-Host "✅ SUCCESS!" -ForegroundColor Green
    Write-Host ""
    Write-Host "📊 RESPONSE SUMMARY:" -ForegroundColor Cyan
    Write-Host "  Case ID: $($resp.case_id)"
    Write-Host "  Crime Type: $($resp.crime_type)"
    Write-Host "  Template: $($resp.template_name)"
    Write-Host "  Timestamp: $($resp.timestamp)"
    Write-Host "  LLM Provider: $($resp.llm_provider)"
    Write-Host "  Stages Completed: $($resp.stages.Count)"
    
    if ($resp.error) {
        $errMsg = $resp.error
        if ($errMsg.length -gt 150) {
            $errMsg = $errMsg.substring(0, 150) + "..."
        }
        Write-Host "  ⚠️  Error: $errMsg" -ForegroundColor Yellow
    } else {
        Write-Host "  ✅ No errors" -ForegroundColor Green
    }
    
    Write-Host ""
    Write-Host "📄 FULL RESPONSE (JSON):" -ForegroundColor Green
    $json_out = $resp | ConvertTo-Json -Depth 5
    Write-Host $json_out
    
} catch {
    Write-Host "❌ ERROR:" -ForegroundColor Red
    Write-Host $_.Exception.Message
}

Write-Host ""
Write-Host "✅ Test complete!" -ForegroundColor Green
