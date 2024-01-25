Write-Host "  Get workspace url..." -ForegroundColor DarkYellow
$workspaceUrl = az resource show `
  --resource-group $resourceGroupName `
  --name $databricksName `
  --resource-type "Microsoft.Databricks/workspaces" `
  --query properties.workspaceUrl `
  --out tsv

Throw-WhenError -output $workspaceUrl
Write-Host "    Url: $workspaceUrl" -ForegroundColor DarkYellow

Write-Host "  Generate .databrickscfg" -ForegroundColor DarkYellow
Set-Content ~/.databrickscfg "[DEFAULT]"
Add-Content ~/.databrickscfg "host = $workspaceUrl"
Add-Content ~/.databrickscfg "azure_tenant_id = $tenantId"
Add-Content ~/.databrickscfg "azure_client_id = $pipelineClientId"
Add-Content ~/.databrickscfg "azure_client_secret = $pipelineSecret"