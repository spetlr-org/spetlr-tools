
# Important Paths
$repoRoot = (git rev-parse --show-toplevel)

# at some point, the following will be made variable between deployments
$resourceName                 = "githubspetlrtools$uniqueRunId"
$resourceGroupName            = $resourceName
$tenantId = (az account show | ConvertFrom-Json).tenantId

$databricksName               = $resourceName

# Use eastus because of free azure subscription
# note, we no longer use a free subscription
$location                     = "swedencentral"

$resourceTags = @{
  "Owner"      = "Auto Deployed"
  "System"     = "SPETLR-ORG"
  "Service"    = "Spetlr tools"
  "deployedAt" = "$(Get-Date -Format "o" -AsUTC)"
}
$resourceTagsJson = ($resourceTags | ConvertTo-Json -Depth 4 -Compress)
