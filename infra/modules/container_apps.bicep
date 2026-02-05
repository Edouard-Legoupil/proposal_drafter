
// modules/container_apps.bicep
@description('The location for the container apps.')
param location string

@description('The prefix for the container apps.')
param prefix string

@description('The name of the container registry.')
param containerRegistry string

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

@description('The Docker image for the backend app.')
param backendImage string

@description('The ID of the container app environment.')
param environmentId string

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

var backendAppName = '${prefix}-app'

resource backendApp 'Microsoft.App/containerApps@2022-03-01' = {
  name: backendAppName
  location: location
  tags: {
    Environment: 'Dev'
  }
  properties: {
    managedEnvironmentId: environmentId
    configuration: {
      ingress: {
        external: true
        targetPort: 8000
      }
      registries: [
        {
          server: '${containerRegistry}.azurecr.io'
          username: containerRegistry
          passwordSecretRef: 'acr-password'
        }
      ]
      secrets: [
        {
          name: 'acr-password'
          value: listCredentials(resourceId('Microsoft.ContainerRegistry/registries', containerRegistry), '2022-02-01-preview').passwords[0].value
        }
        {
          name: 'postgres-connection-string'
          value: 'postgresql://${postgresAdminUser}:${postgresAdminPassword}@${postgresServerName}.postgres.database.azure.com/${postgresDatabaseName}'
        }
        {
          name: 'redis-connection-string'
          value: 'redis://default:${redisPassword}@${redisHost}:${redisPort}'
        }
        {
          name: 'openai-endpoint'
          value: openAiEndpoint
        }
        {
          name: 'openai-api-key'
          value: openAiApiKey
        }
        {
          name: 'serper-api-key'
          value: serperApiKey
        }
        {
          name: 'entra-tenant-id'
          value: entraTenantId
        }
        {
          name: 'entra-client-id'
          value: entraClientId
        }
        {
          name: 'entra-client-secret'
          value: entraClientSecret
        }
        {
          name: 'secret-key'
          value: secretKey
        }
        {
          name: 'cf-access-client-id'
          value: cfAccessClientId
        }
        {
          name: 'cf-access-client-secret'
          value: cfAccessClientSecret
        }
      ]
    }
    template: {
      containers: [
        {
          image: '${containerRegistry}.azurecr.io/${backendImage}'
          name: 'backend'
          resources: {
            cpu: json('0.5')
            memory: '1.0Gi'
          }
          env: [
            {
              name: 'DATABASE_URL'
              secretRef: 'postgres-connection-string'
            }
            {
              name: 'REDIS_URL'
              secretRef: 'redis-connection-string'
            }
            {
              name: 'AZURE_OPENAI_ENDPOINT'
              secretRef: 'openai-endpoint'
            }
            {
              name: 'AZURE_OPENAI_API_KEY'
              secretRef: 'openai-api-key'
            }
            {
              name: 'SERPER_API_KEY'
              secretRef: 'serper-api-key'
            }
            {
              name: 'ENTRA_TENANT_ID'
              secretRef: 'entra-tenant-id'
            }
            {
              name: 'ENTRA_CLIENT_ID'
              secretRef: 'entra-client-id'
            }
            {
              name: 'ENTRA_CLIENT_SECRET'
              secretRef: 'entra-client-secret'
            }
            {
              name: 'SECRET_KEY'
              secretRef: 'secret-key'
            }
            {
              name: 'CF_ACCESS_CLIENT_ID'
              secretRef: 'cf-access-client-id'
            }
            {
              name: 'CF_ACCESS_CLIENT_SECRET'
              secretRef: 'cf-access-client-secret'
            }
          ]
        }
      ]
      scale: {
        minReplicas: 1
        maxReplicas: 3
      }
    }
  }
}

output appUrl string = backendApp.properties.configuration.ingress.fqdn
