param (
  [Parameter(Mandatory=$true)]
  [ValidateNotNullOrEmpty()]
  [string]
  $tenantId,

  [Parameter(Mandatory=$true)]
  [ValidateNotNullOrEmpty()]
  [string]
  $pipelineClientId,

  [Parameter(Mandatory=$true)]
  [ValidateNotNullOrEmpty()]
  [string]
  $pipelineSecret,

  [Parameter(Mandatory=$false)]
  [string]
  $uniqueRunId=''
)

$repoRoot = (git rev-parse --show-toplevel)

. "$repoRoot/.github/deploy/steps/00-Config.ps1"
. "$repoRoot/.github/deploy/Utilities/all.ps1"

Write-Host "  Collect resourceId and workspace URL" -ForegroundColor DarkYellow
$resourceId = az resource show `
  --resource-group $resourceGroupName `
  --name $databricksName `
  --resource-type "Microsoft.Databricks/workspaces" `
  --query id `
  --out tsv

Throw-WhenError -output $resourceId

Write-Host "  Get workspace url..." -ForegroundColor DarkYellow
$workspaceUrl = az resource show `
  --resource-group $resourceGroupName `
  --name $databricksName `
  --resource-type "Microsoft.Databricks/workspaces" `
  --query properties.workspaceUrl `
  --out tsv

Throw-WhenError -output $workspaceUrl

Write-Host "    Url: $workspaceUrl" -ForegroundColor DarkYellow

Write-Host "  Generate .databrickscfg for databricks CLI v1" -ForegroundColor DarkYellow

Write-Host "  Add the SPN to the Databricks Workspace as an admin user" -ForegroundColor DarkYellow
$accessToken = Set-DatabricksSpnAdminUser `
  -tenantId $tenantId `
  -clientId $pipelineClientId `
  -clientSecret $pipelineSecret `
  -workspaceUrl $workspaceUrl `
  -resourceId $resourceId

Throw-WhenError -output $accessToken

Write-Host "  Generate SPN personal access token" -ForegroundColor DarkYellow
$token = ConvertTo-DatabricksPersonalAccessToken `
  -workspaceUrl $workspaceUrl `
  -bearerToken $accessToken `
  -tokenComment "$tokenComment"

Throw-WhenError -output $token

Write-Host "  Generate .databrickscfg" -ForegroundColor DarkYellow
Set-Content ~/.databrickscfg "[DEFAULT]"
Add-Content ~/.databrickscfg "host = https://$workspaceUrl"
Add-Content ~/.databrickscfg "token = $token"
Add-Content ~/.databrickscfg ""