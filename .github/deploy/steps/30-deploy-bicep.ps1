
Write-Host "  Deploying ressources using Bicep..." -ForegroundColor Yellow

# the following settings were moved here from 00-Config to keep the config file free of any
# command that is slow or that can fail. This is to keep the destroy script, which also
# depends on 00-Config as fast and as reliable as possible.

$output = az bicep build --file $repoRoot\.github\deploy-bicep\main-spetlrtools.bicep
Throw-WhenError -output $output


$output = az deployment sub create `
  --name $resourceGroupName `
  --location $location `
  --template-file $repoRoot\.github\deploy-bicep\main-spetlrtools.bicep `
  --parameters `
      location=$location `
      tags=$resourceTagsJson `
      resourceGroupName=$resourceGroupName `
      databricksName=$databricksName

Throw-WhenError -output $output

Write-Host "  Ressources deployed!" -ForegroundColor Green
