
// modules/container_env.bicep
@description('The location for the container app environment.')
param location string

@description('The prefix for the container app environment name.')
param prefix string

var containerAppEnvName = '${prefix}-env-${uniqueString(resourceGroup().id)}'

resource containerAppEnv 'Microsoft.App/managedEnvironments@2022-03-01' = {
  name: containerAppEnvName
  location: location
  tags: {
    Environment: 'Dev'
  }
  properties: {}
}

output id string = containerAppEnv.id
