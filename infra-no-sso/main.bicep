@description('The location for all resources.')
param location string = resourceGroup().location

@description('A common prefix for all resource names.')
param resourcePrefix string = 'proposalgen'

@description('The Docker image for the backend app.')
param backendImage string = 'backend:latest'

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
param secretKey string

@secure()
param cfAccessClientSecret string 

@secure()
param cfAccessClientId string

@secure()
param postgresAdminPassword string = newGuid()

// Common tags
var commonTags = {
  EnvironmentSize: environmentSize
  Project: resourcePrefix
}

// --------------------
// Log Analytics Workspace
// --------------------
var logAnalyticsName = '${resourcePrefix}-law-${uniqueString(resourceGroup().id)}'

resource logAnalytics 'Microsoft.OperationalInsights/workspaces@2022-10-01' = {
  name: logAnalyticsName
  location: location
  sku: {
    name: 'PerGB2018'
  }
  properties: {
    retentionInDays: 30
  }
  tags: commonTags
}

// --------------------
// Azure Container Registry
// --------------------
var acrName = '${resourcePrefix}acr${uniqueString(resourceGroup().id)}'

resource acr 'Microsoft.ContainerRegistry/registries@2023-01-01-preview' = {
  name: acrName
  location: location
  sku: {
    name: 'Basic'
  }
  properties: {
    adminUserEnabled: true
  }
  tags: commonTags
}

// --------------------
// Azure OpenAI Account
// --------------------
var openAiAccountName = '${resourcePrefix}-openai-${uniqueString(resourceGroup().id)}'

resource openAiAccount 'Microsoft.CognitiveServices/accounts@2023-05-01' = {
  name: openAiAccountName
  location: location
  sku: {
    name: 'S0'
  }
  kind: 'OpenAI'
  properties: {
    publicNetworkAccess: 'Enabled'
  }
  tags: commonTags
}

// GPT-4o deployment
resource gpt4o 'Microsoft.CognitiveServices/accounts/deployments@2023-05-01' = {
  name: 'gpt-4o'
  parent: openAiAccount
  sku: {
    name: 'GlobalStandard'
    capacity: 10
  }
  properties: {
    model: {
      format: 'OpenAI'
      name: 'gpt-4o'
      version: '2024-05-13'
    }
  }
}

// text-embedding-ada-002 deployment
resource embedAda 'Microsoft.CognitiveServices/accounts/deployments@2023-05-01' = {
  name: 'text-embedding-ada-002'
  parent: openAiAccount
  sku: {
    name: 'GlobalStandard'
    capacity: 10
  }
  properties: {
    model: {
      format: 'OpenAI'
      name: 'text-embedding-ada-002'
      version: '2'
    }
  }
}

// --------------------
// PostgreSQL Flexible Server
// --------------------
var postgresServerName = '${resourcePrefix}-postgres-${uniqueString(resourceGroup().id)}'
var postgresDatabaseName = 'proposalgen_db'

resource postgresServer 'Microsoft.DBforPostgreSQL/flexibleServers@2023-03-01-preview' = {
  name: postgresServerName
  location: location
  sku: {
    name: 'Standard_D2ds_v4'
    tier: 'GeneralPurpose'
  }
  properties: {
    administratorLogin: 'psqladmin'
    administratorLoginPassword: postgresAdminPassword
    version: '14'
    storage: {
      autoGrow: 'Enabled'
      storageSizeGB: 32
    }
    highAvailability: {
      mode: 'Disabled'
    }
    backup: {
      backupRetentionDays: 7
      geoRedundantBackup: 'Disabled'
    }
  }
  tags: commonTags
}

resource postgresDatabase 'Microsoft.DBforPostgreSQL/flexibleServers/databases@2023-03-01-preview' = {
  parent: postgresServer
  name: postgresDatabaseName
  properties: {
    charset: 'UTF8'
    collation: 'en_US.UTF8'
  }
}

resource postgresFirewall 'Microsoft.DBforPostgreSQL/flexibleServers/firewallRules@2023-03-01-preview' = {
  parent: postgresServer
  name: 'allow-azure'
  properties: {
    startIpAddress: '0.0.0.0'
    endIpAddress: '0.0.0.0'
  }
}

// --------------------
// Redis Cache
// --------------------
var redisCacheName = '${resourcePrefix}-redis-${uniqueString(resourceGroup().id)}'

resource redisCache 'Microsoft.Cache/Redis@2023-08-01' = {
  name: redisCacheName
  location: location
  sku: {
    name: 'Standard'
    family: 'C'
    capacity: 1
  }
  properties: {
    redisVersion: '6'
    enableNonSslPort: false
    publicNetworkAccess: 'Enabled'
  }
  tags: commonTags
}

// --------------------
// Container Apps Environment with Monitoring
// --------------------
var containerEnvName = '${resourcePrefix}-env'

resource containerEnv 'Microsoft.App/managedEnvironments@2022-03-01' = {
  name: containerEnvName
  location: location
  sku: {
    name: 'Consumption'
  }
  properties: {
    appLogsConfiguration: {
      destination: 'log-analytics'
      logAnalyticsConfiguration: {
        customerId: logAnalytics.properties.customerId
        sharedKey: listKeys(logAnalytics.id, '2022-10-01').primarySharedKey
      }
    }
  }
  tags: commonTags
}

// --------------------
// Container App with Autoscaling
// --------------------
var containerAppName = '${resourcePrefix}-backend'

resource containerApp 'Microsoft.App/containerApps@2023-05-01' = {
  name: containerAppName
  location: location
  properties: {
    managedEnvironmentId: containerEnv.id
    configuration: {
      ingress: {
        external: true
        targetPort: 80
      }
      registries: [
        {
          server: acr.properties.loginServer
          username: listCredentials(acr.id, '2023-01-01-preview').username
          passwordSecretRef: 'acr-password'
        }
      ]
      secrets: [
        { name: 'acr-password', value: listCredentials(acr.id, '2023-01-01-preview').passwords[0].value }
        { name: 'postgres-password', value: postgresAdminPassword }
        { name: 'redis-password', value: listKeys(redisCache.id, '2023-08-01').primaryKey }
        { name: 'openai-key', value: listKeys(openAiAccount.id, '2023-05-01').key1 }
        { name: 'serper-api-key', value: serperApiKey }
        { name: 'secret-key', value: secretKey }
        { name: 'cf-access-client-id', value: cfAccessClientId }
        { name: 'cf-access-client-secret', value: cfAccessClientSecret }
      ]
    }
    template: {
      containers: [
        {
          name: 'backend'
          image: '${acr.properties.loginServer}/${backendImage}'

          env: [
            // --- Database ---
            { name: 'DB_USERNAME', value: postgresServer.properties.administratorLogin }
            { name: 'DB_PASSWORD', secretRef: 'postgres-password' }
            { name: 'DB_NAME', value: postgresDatabase.name }
            { name: 'DB_HOST', value: postgresServer.name }
            { name: 'DB_PORT', value: '5432' }

            // --- Azure OpenAI Chat ---
            { name: 'AZURE_OPENAI_ENDPOINT', value: openAiAccount.properties.endpoint }
            { name: 'OPENAI_API_VERSION', value: '2024-05-13' }
            { name: 'AZURE_OPENAI_API_KEY', secretRef: 'openai-key' }
            { name: 'AZURE_DEPLOYMENT_NAME', value: 'gpt-4o' }

            // --- Azure OpenAI Embeddings ---
            { name: 'AZURE_EMBEDDING_MODEL', value: 'text-embedding-ada-002' }
            { name: 'AZURE_OPENAI_ENDPOINT_EMBED', value: openAiAccount.properties.endpoint }
            { name: 'AZURE_OPENAI_API_KEY_EMBED', secretRef: 'openai-key' }
            { name: 'AZURE_EMBEDDING_DEPLOYMENT_NAME', value: 'text-embedding-ada-002' }
            { name: 'AZURE_OPENAI_API_VERSION_EMBED', value: '2' }

            // --- Redis ---
            { name: 'REDIS_HOST', value: redisCache.properties.hostName }
            { name: 'REDIS_PORT', value: string(redisCache.properties.sslPort) }
            { name: 'REDIS_PASSWORD', secretRef: 'redis-password' }

            // --- Security + APIs ---
            { name: 'SECRET_KEY', secretRef: 'secret-key' }
            { name: 'SERPER_API_KEY', secretRef: 'serper-api-key' }

            // --- Cloudflare ---
            { name: 'CF_ACCESS_CLIENT_ID', secretRef: 'cf-access-client-id' }
            { name: 'CF_ACCESS_CLIENT_SECRET', secretRef: 'cf-access-client-secret' }

          ]
        }
      ]
      scale: {
        minReplicas: 1
        maxReplicas: 5
        rules: [
          {
            name: 'cpu-scale'
            custom: {
              type: 'cpu'
              metadata: {
                value: '70'
              }
            }
          }
          {
            name: 'memory-scale'
            custom: {
              type: 'memory'
              metadata: {
                value: '80'
              }
            }
          }
          {
            name: 'http-scale'
            http: {
              metadata: {
                concurrentRequests: '50'
              }
            }
          }
        ]
      }
    }
  }
  tags: commonTags
}

// --------------------
// Outputs
// --------------------
output acrName string = acr.name
output openAiEndpoint string = openAiAccount.properties.endpoint
@secure()
output openAiApiKey string = listKeys(openAiAccount.id, '2023-05-01').key1

output postgresServerName string = postgresServer.name
output postgresDatabaseName string = postgresDatabase.name
output postgresAdminUser string = postgresServer.properties.administratorLogin
@secure()
output postgresAdminPassword string = postgresAdminPassword

output redisHost string = redisCache.properties.hostName
output redisPort int = redisCache.properties.sslPort
@secure()
output redisPassword string = listKeys(redisCache.id, '2023-08-01').primaryKey

output containerAppUrl string = containerApp.properties.configuration.ingress.fqdn
