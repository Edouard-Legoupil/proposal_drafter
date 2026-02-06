
// main.bicep
@description('The location for all resources.')
param location string = resourceGroup().location

@description('A common prefix for all resource names.')
param resourcePrefix string = 'proposalgen'

@description('The Docker image for the backend app.')
param backendImage string = 'backend:latest'


@description('The size of the environment to deploy.')
@allowed([
  'Testing'
  'Exploratory'
  'Expanded'
  'Organization-Wide'
])
param environmentSize string = 'Testing'

@secure()
param serperApiKey string
@secure()
param entraTenantId string
@secure()
param entraClientId string
@secure()
param entraClientSecret string

@secure()
param secretKey string

param cfAccessClientId string

@secure()
param cfAccessClientSecret string

// Shared Resources
module postgres 'modules/postgres.bicep' = {
  name: 'postgresDeployment'
  params: {
    location: location
    prefix: resourcePrefix
    environmentSize: environmentSize
  }
}

module redis 'modules/redis.bicep' = {
  name: 'redisDeployment'
  params: {
    location: location
    prefix: resourcePrefix
    environmentSize: environmentSize
  }
}

module openAi 'modules/openai.bicep' = {
  name: 'openAiDeployment'
  params: {
    location: location
    prefix: resourcePrefix
  }
}

// App Service
module appService 'modules/app_service.bicep' = {
  name: 'appServiceDeployment'
  params: {
    location: location
    prefix: resourcePrefix
    environmentSize: environmentSize
    postgresServerName: postgres.outputs.serverName
    postgresDatabaseName: postgres.outputs.databaseName
    postgresAdminUser: postgres.outputs.adminUser
    postgresAdminPassword: postgres.outputs.adminPassword
    redisHost: redis.outputs.hostName
    redisPort: redis.outputs.port
    redisPassword: redis.outputs.password
    openAiEndpoint: openAi.outputs.endpoint
    openAiApiKey: openAi.outputs.apiKey
    serperApiKey: serperApiKey
    entraTenantId: entraTenantId
    entraClientId: entraClientId
    entraClientSecret: entraClientSecret
    secretKey: secretKey
    cfAccessClientId: cfAccessClientId
    cfAccessClientSecret: cfAccessClientSecret
  }
}

// Outputs
output postgresServerName string = postgres.outputs.serverName
output appUrl string = appService.outputs.appUrl
