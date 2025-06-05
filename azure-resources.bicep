@description('Base name for all resources')
param baseName string

@description('Database name')
param databaseName string = 'postgres' 

@description('Location for all resources')
param location string = resourceGroup().location

@description('Existing App Service Plan name')
param existingAppServicePlanName string

@description('Existing PostgreSQL server name')
param existingPostgresServerName string

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

@description('Azure OpenAI Endpoint for Embeddings')
param azureOpenAiEndpointEmbed string

@description('Azure OpenAI API Key for Embeddings')
@secure()
param azureOpenAiApiKeyEmbed string

@description('Azure OpenAI API Version for Embeddings')
param azureOpenAiApiVersionEmbed string

@description('Azure Embedding Deployment Name')
param azureEmbeddingDeploymentName string

@description('Secret Key for JWT Authentication')
@secure()
param secretKey string

@description('PostgreSQL admin username')
param postgresAdminLogin string = 'postgresadmin'

@description('PostgreSQL admin password')
@secure()
param postgresAdminPassword string

@description('Redis Host')
param redisHost string

@description('Redis Password')
@secure()
param redisPassword string

// ============================================================================
// NEW: Process Docker Compose file and replace ALL variables with actual values
// ============================================================================
var dockerComposeContent = replace(
  replace(
    replace(
      replace(
        replace(
          replace(
            replace(
              replace(
                replace(
                  replace(
                    replace(
                      replace(
                        replace(
                          replace(
                            replace(
                              replace(
                                replace(
                                  loadTextContent('azure-docker-compose.yml'),
                                  '\${ACR_REGISTRY_URL}', dockerRegistryServerUrl
                                ),  // 1st replace
                                '\${AZURE_OPENAI_ENDPOINT}', azureOpenAiEndpoint
                              ),  // 2nd replace
                              '\${AZURE_OPENAI_API_KEY}', azureOpenAiApiKey
                            ),  // 3rd replace
                            '\${OPENAI_API_VERSION}', openAiApiVersion
                          ),  // 4th replace
                          '\${AZURE_DEPLOYMENT_NAME}', azureDeploymentName
                        ),  // 5th replace
                        '\${AZURE_OPENAI_ENDPOINT_EMBED}', azureOpenAiEndpointEmbed
                      ),  // 6th replace
                      '\${AZURE_OPENAI_API_KEY_EMBED}', azureOpenAiApiKeyEmbed
                    ),  // 7th replace
                    '\${AZURE_OPENAI_API_VERSION_EMBED}', azureOpenAiApiVersionEmbed
                  ),  // 8th replace
                  '\${AZURE_EMBEDDING_DEPLOYMENT_NAME}', azureEmbeddingDeploymentName
                ),  // 9th replace
                '\${DB_USERNAME}', 'iom_uc1_user'
              ),  // 10th replace
              '\${DB_PASSWORD}', 'IomUC1@20250604$'
            ),  // 11th replace
            '\${DB_NAME}', databaseName
          ),  // 12th replace
          '\${DB_HOST}', reference(
            resourceId('Microsoft.DBforPostgreSQL/flexibleServers', existingPostgresServerName),
            '2025-01-01-preview'
          ).fullyQualifiedDomainName
        ),  // 13th replace
        '\${DB_PORT}', '5432'
      ),  // 14th replace
      '\${SECRET_KEY}', secretKey
    ),  // 15th replace
    '\${REDIS_HOST}', redisHost
  ),  // 16th replace
  '\${REDIS_PASSWORD}', redisPassword  // 17th replace
)

// Web App for Containers (Multi-container)
resource webApp 'Microsoft.Web/sites@2023-12-01' = {
  name: '${baseName}-app'
  location: location
  properties: {
    serverFarmId: resourceId('Microsoft.Web/serverfarms', existingAppServicePlanName)
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
          name: 'ACR_REGISTRY_URL'
          value: dockerRegistryServerUrl
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
          name: 'AZURE_OPENAI_ENDPOINT_EMBED'
          value: azureOpenAiEndpointEmbed
        }
        {
          name: 'AZURE_OPENAI_API_KEY_EMBED'
          value: azureOpenAiApiKeyEmbed
        }
        {
          name: 'AZURE_OPENAI_API_VERSION_EMBED'
          value: azureOpenAiApiVersionEmbed
        }
        {
          name: 'AZURE_EMBEDDING_DEPLOYMENT_NAME'
          value: azureEmbeddingDeploymentName
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
          value: databaseName
        }
        {
          name: 'POSTGRES_HOST'
          value: reference(resourceId('Microsoft.DBforPostgreSQL/flexibleServers', existingPostgresServerName), '2025-01-01-preview').fullyQualifiedDomainName
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
          value: 'IomUC1@20250604'
        }
        {
          name: 'DB_NAME'
          value: databaseName
        }
        {
          name: 'DB_HOST'
          value: reference(resourceId('Microsoft.DBforPostgreSQL/flexibleServers', existingPostgresServerName), '2025-01-01-preview').fullyQualifiedDomainName
        }
        {
          name: 'DB_PORT'
          value: '5432'
        }
        {
          name: 'REDIS_HOST'
          value: redisHost
        }
        {
          name: 'REDIS_PASSWORD'
          value: redisPassword
        }
        {
          name: 'VITE_BACKEND_URL'
          value: 'https://${baseName}-app.azurewebsites.net/api'
        }
      ]
      linuxFxVersion: 'COMPOSE|${base64(dockerComposeContent)}'
    }
  }
}

output appServiceUrl string = 'https://${webApp.properties.defaultHostName}'
output postgresServerName string = existingPostgresServerName
output postgresServerFqdn string = reference(resourceId('Microsoft.DBforPostgreSQL/flexibleServers', existingPostgresServerName), '2025-01-01-preview').fullyQualifiedDomainName
