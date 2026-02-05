
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
module acr 'modules/acr.bicep' = {
  name: 'acrDeployment'
  params: {
    location: location
    prefix: resourcePrefix
    environmentSize: environmentSize
  }
}

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

// Container App Environment
module containerEnv 'modules/container_env.bicep' = {
  name: 'containerEnvDeployment'
  params: {
    location: location
    prefix: resourcePrefix
  }
}

// Container Apps
module containerApps 'modules/container_apps.bicep' = {
  name: 'containerAppsDeployment'
  params: {
    location: location
    prefix: resourcePrefix
    containerRegistry: acr.outputs.name
    postgresServerName: postgres.outputs.serverName
    postgresDatabaseName: postgres.outputs.databaseName
    postgresAdminUser: postgres.outputs.adminUser
    postgresAdminPassword: postgres.outputs.adminPassword
    redisHost: redis.outputs.hostName
    redisPort: redis.outputs.port
    redisPassword: redis.outputs.password
    backendImage: backendImage
    environmentId: containerEnv.outputs.id
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
output acrName string = acr.outputs.name
output postgresServerName string = postgres.outputs.serverName
output containerAppUrl string = containerApps.outputs.appUrl
