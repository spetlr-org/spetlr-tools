Write-Host "Test 02: Fetch test job!" -ForegroundColor DarkYellow

Write-Host "   Wait 2 min for things to settle..." -ForegroundColor DarkYellow
Start-Sleep -s 120
spetlr-test-job fetch --runid-json "$repoRoot/test_01_details.json"