Write-Host "Test 01: Submit test job!" -ForegroundColor DarkYellow

spetlr-test-job submit `
        --tests "$repoRoot/tests/" `
        --tasks-from "$repoRoot/tests/cluster/" `
        --cluster-file "$repoRoot/.github/databricks-configs/cluster.json" `
        --requirements-file "$repoRoot/.github/databricks-configs/clustertest_requirements.txt" `
        --sparklibs-file "$repoRoot/.github/databricks-configs/sparklibs.json" `
        --out-json "$repoRoot/test_01_details.json"

