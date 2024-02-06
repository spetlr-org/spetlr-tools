param databricksName string
param location string
param resourceGroupName string
param resourceTags object
//#############################################################################################
//# Provision Databricks Workspace
//#############################################################################################

resource rsdatabricks 'Microsoft.Databricks/workspaces@2022-04-01-preview' = {
  name: databricksName
  location: location
  properties: {
    managedResourceGroupId: subscriptionResourceId('Microsoft.Resources/resourceGroups', '${resourceGroupName}Cluster')
  }
  tags: resourceTags
}
