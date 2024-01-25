Write-Host "Running spetlr-tool tests" -ForegroundColor DarkYellow

$repoRoot = (git rev-parse --show-toplevel)


Get-ChildItem "$PSScriptRoot/tests" -Filter *.ps1 | Sort-Object name | Foreach-Object {
    Write-Host "###### Now running test: $_"
    . ("$_")
  }

Write-Host "spetlr-tool tests success!" -ForegroundColor Green