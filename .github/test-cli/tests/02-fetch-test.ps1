Write-Host "Test 02: Fetch test job!" -ForegroundColor DarkYellow

Write-Host "   Wait 10s for things to settle..." -ForegroundColor DarkYellow
Start-Sleep -s 10
spetlr-test-job fetch --runid-json "$repoRoot/test_01_details.json"