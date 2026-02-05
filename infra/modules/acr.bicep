
// modules/acr.bicep
@description('The location for the container registry.')
param location string

@description('The prefix for the container registry name.')
param prefix string

var acrName = '${prefix}acr${uniqueString(resourceGroup().id)}'

resource acr 'Microsoft.ContainerRegistry/registries@2022-02-01-preview' = {
  name: acrName
  location: location
  sku: {
    name: 'Standard'
  }
  tags: {
    Environment: 'Dev'
  }
  properties: {
    adminUserEnabled: true
  }
}

output name string = acr.name
