
// modules/app_service.bicep
@description('The location for the App Service.')
param location string

@description('The prefix for the App Service names.')
param prefix string

@description('The size of the environment.')
param environmentSize string

@description('The PostgreSQL server name.')
param postgresServerName string

@description('The PostgreSQL database name.')
param postgresDatabaseName string

@description('The PostgreSQL admin user.')
param postgresAdminUser string

@secure()
@description('The PostgreSQL admin password.')
param postgresAdminPassword string

@description('The Redis host name.')
param redisHost string

@description('The Redis port.')
param redisPort int

@secure()
@description('The Redis password.')
param redisPassword string

@description('The Azure OpenAI endpoint.')
param openAiEndpoint string

@secure()
@description('The Azure OpenAI API key.')
param openAiApiKey string

@secure()
@description('The Serper API key.')
param serperApiKey string

@secure()
@description('The Entra Tenant ID for SSO.')
param entraTenantId string

@secure()
@description('The Entra Client ID for SSO.')
param entraClientId string

@secure()
@description('The Entra Client Secret for SSO.')
param entraClientSecret string

@secure()
@description('The Django secret key.')
param secretKey string

@description('Cloudflare Access Client ID.')
param cfAccessClientId string

@secure()
@description('Cloudflare Access Client Secret.')
param cfAccessClientSecret string

var appServicePlanName = '${prefix}-plan-${uniqueString(resourceGroup().id)}'
var webAppName = '${prefix}-app-${uniqueString(resourceGroup().id)}'

var skus = {
  Testing: {
    name: 'B1'
    tier: 'Basic'
  }
  Exploratory: {
    name: 'B1'
    tier: 'Basic'
  }
  Expanded: {
    name: 'P1v2'
    tier: 'PremiumV2'
  }
  'Organization-Wide': {
    name: 'P1v3'
    tier: 'PremiumV3'
  }
}

resource appServicePlan 'Microsoft.Web/serverfarms@2022-03-01' = {
  name: appServicePlanName
  location: location
  sku: skus[environmentSize]
  kind: 'linux'
  properties: {
    reserved: true
  }
  tags: {
    Environment: 'Dev'
  }
}

resource webApp 'Microsoft.Web/sites@2022-03-01' = {
  name: webAppName
  location: location
  kind: 'app,linux,python'
  properties: {
    serverFarmId: appServicePlan.id
    siteConfig: {
      linuxFxVersion: 'PYTHON|3.11'
      appCommandLine: 'chmod +x /home/site/wwwroot/infra/startup.sh && /home/site/wwwroot/infra/startup.sh'
      appSettings: [
        {
          name: 'DB_HOST'
          value: '${postgresServerName}.postgres.database.azure.com'
        }
        {
          name: 'DB_NAME'
          value: postgresDatabaseName
        }
        {
          name: 'DB_USERNAME'
          value: postgresAdminUser
        }
        {
          name: 'DB_PASSWORD'
          value: postgresAdminPassword
        }
        {
          name: 'DATABASE_URL'
          value: 'postgresql://${postgresAdminUser}:${postgresAdminPassword}@${postgresServerName}.postgres.database.azure.com/${postgresDatabaseName}'
        }
        {
          name: 'REDIS_URL'
          value: 'redis://default:${redisPassword}@${redisHost}:${redisPort}'
        }
        {
          name: 'AZURE_OPENAI_ENDPOINT'
          value: openAiEndpoint
        }
        {
          name: 'AZURE_OPENAI_API_KEY'
          value: openAiApiKey
        }
        {
          name: 'SERPER_API_KEY'
          value: serperApiKey
        }
        {
          name: 'ENTRA_TENANT_ID'
          value: entraTenantId
        }
        {
          name: 'ENTRA_CLIENT_ID'
          value: entraClientId
        }
        {
          name: 'ENTRA_CLIENT_SECRET'
          value: entraClientSecret
        }
        {
          name: 'SECRET_KEY'
          value: secretKey
        }
        {
          name: 'CF_ACCESS_CLIENT_ID'
          value: cfAccessClientId
        }
        {
          name: 'CF_ACCESS_CLIENT_SECRET'
          value: cfAccessClientSecret
        }
        {
          name: 'SCM_DO_BUILD_DURING_DEPLOYMENT'
          value: 'true'
        }
        {
          name: 'PYTHONPATH'
          value: '/home/site/wwwroot'
        }
        {
          name: 'PORT'
          value: '8000'
        }
      ]
      alwaysOn: (environmentSize != 'Testing' && environmentSize != 'Exploratory')
      http20Enabled: true
    }
    httpsOnly: true
  }
  tags: {
    Environment: 'Dev'
  }
}

output appUrl string = webApp.properties.defaultHostName
