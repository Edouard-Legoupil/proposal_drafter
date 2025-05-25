@description('Base name for all resources')
param baseName string = 'proposalgen'

@description('Location for all resources')
param location string = resourceGroup().location

@description('App Service Plan SKU')
param appServicePlanSku object = {
  name: 'P1v3'
  tier: 'PremiumV3'
  size: 'P1v3'
  family: 'Pv3'
  capacity: 1
}

@description('Docker registry server URL')
param dockerRegistryServerUrl string

@description('Docker registry server username')
@secure()
param dockerRegistryServerUsername string

@description('Docker registry server password')
@secure()
param dockerRegistryServerPassword string

@description('Azure OpenAI Endpoint')
param azureOpenAiEndpoint string

@description('Azure OpenAI API Key')
@secure()
param azureOpenAiApiKey string

@description('OpenAI API Version')
param openAiApiVersion string

@description('Azure OpenAI Deployment Name')
param azureDeploymentName string

@description('Secret Key for JWT Authentication')
@secure()
param secretKey string

@description('PostgreSQL admin username')
param postgresAdminLogin string = 'postgresadmin'

@description('PostgreSQL admin password')
@secure()
param postgresAdminPassword string

// App Service Plan
resource appServicePlan 'Microsoft.Web/serverfarms@2021-03-01' = {
  name: '${baseName}-plan'
  location: location
  sku: appServicePlanSku
  kind: 'linux'
  properties: {
    reserved: true
  }
}

// Azure Database for PostgreSQL
resource postgresServer 'Microsoft.DBforPostgreSQL/flexibleServers@2021-06-01' = {
  name: '${baseName}-db'
  location: location
  sku: {
    name: 'Standard_B1ms'
    tier: 'Burstable'
  }
  properties: {
    version: '15'
    administratorLogin: postgresAdminLogin
    administratorLoginPassword: postgresAdminPassword
    storage: {
      storageSizeGB: 32
    }
  }
}

// Create a database in PostgreSQL server
resource database 'Microsoft.DBforPostgreSQL/flexibleServers/databases@2021-06-01' = {
  name: 'proposalgen'
  parent: postgresServer
}

// Firewall rule to allow Azure services
resource firewallRule 'Microsoft.DBforPostgreSQL/flexibleServers/firewallRules@2021-06-01' = {
  name: 'AllowAllAzureIPs'
  parent: postgresServer
  properties: {
    startIpAddress: '0.0.0.0'
    endIpAddress: '255.255.255.255'
  }
}

// Web App for Containers (Multi-container)
resource webApp 'Microsoft.Web/sites@2021-03-01' = {
  name: '${baseName}-app'
  location: location
  properties: {
    serverFarmId: appServicePlan.id
    siteConfig: {
      appSettings: [
        {
          name: 'DOCKER_REGISTRY_SERVER_URL'
          value: dockerRegistryServerUrl
        }
        {
          name: 'DOCKER_REGISTRY_SERVER_USERNAME'
          value: dockerRegistryServerUsername
        }
        {
          name: 'DOCKER_REGISTRY_SERVER_PASSWORD'
          value: dockerRegistryServerPassword
        }
        {
          name: 'WEBSITES_ENABLE_APP_SERVICE_STORAGE'
          value: 'false'
        }
        {
          name: 'AZURE_OPENAI_ENDPOINT'
          value: azureOpenAiEndpoint
        }
        {
          name: 'AZURE_OPENAI_API_KEY'
          value: azureOpenAiApiKey
        }
        {
          name: 'OPENAI_API_VERSION'
          value: openAiApiVersion
        }
        {
          name: 'AZURE_DEPLOYMENT_NAME'
          value: azureDeploymentName
        }
        {
          name: 'SECRET_KEY'
          value: secretKey
        }
        {
          name: 'POSTGRES_USER'
          value: postgresAdminLogin
        }
        {
          name: 'POSTGRES_PASSWORD'
          value: postgresAdminPassword
        }
        {
          name: 'POSTGRES_DB'
          value: 'proposalgen'
        }
        {
          name: 'POSTGRES_HOST'
          value: postgresServer.properties.fullyQualifiedDomainName
        }
        {
          name: 'POSTGRES_PORT'
          value: '5432'
        }
        {
          name: 'DB_USERNAME'
          value: 'iom_uc1_user'
        }
        {
          name: 'DB_PASSWORD'
          value: 'IomUC1@20250523$'
        }
        {
          name: 'DB_NAME'
          value: 'proposalgen'
        }
        {
          name: 'DB_HOST'
          value: postgresServer.properties.fullyQualifiedDomainName
        }
        {
          name: 'DB_PORT'
          value: '5432'
        }
        {
          name: 'VITE_BACKEND_URL'
          value: 'https://${baseName}-app.azurewebsites.net/api'
        }
      ]
      linuxFxVersion: 'COMPOSE|${base64(loadTextContent('azure-docker-compose.yml'))}'
    }
  }
}

output appServiceUrl string = 'https://${webApp.properties.defaultHostName}'
output postgresServerName string = postgresServer.name
output postgresServerFqdn string = postgresServer.properties.fullyQualifiedDomainName
