// Setting target scope
targetScope = 'subscription'

param location string
param resourceTags object
param resourceGroupName string
param databricksName string

// Create integration resource group
module rgModule2 'rg-integration.bicep' = {
  scope: subscription()
  name: '${resourceGroupName}-create'
  params: {
    name: resourceGroupName
    location: location
    tags: resourceTags
  }
}

// Create integration resources
module resources2 'resources-integration.bicep' = {
  name: '${resourceGroupName}-resources-deployment'
  scope: resourceGroup(resourceGroupName)
  dependsOn: [ rgModule2 ]
  params: {
    databricksName: databricksName
    location: location
    resourceGroupName: resourceGroupName
    resourceTags: resourceTags
    }
}
