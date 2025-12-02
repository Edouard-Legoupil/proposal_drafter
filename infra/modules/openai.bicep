
// modules/openai.bicep
@description('The location for the Azure OpenAI service.')
param location string

@description('The prefix for the Azure OpenAI service name.')
param prefix string

var openAiAccountName = '${prefix}-openai-${uniqueString(resourceGroup().id)}'

resource openAiAccount 'Microsoft.CognitiveServices/accounts@2023-05-01' = {
  name: openAiAccountName
  location: location
  sku: {
    name: 'S0'
  }
  kind: 'OpenAI'
  tags: {
    Environment: 'Dev'
  }
  properties: {
    customSubDomainName: openAiAccountName
    publicNetworkAccess: 'Enabled'
  }
}

resource gpt4Deployment 'Microsoft.CognitiveServices/accounts/deployments@2023-05-01' = {
  parent: openAiAccount
  name: 'gpt-4'
  tags: {
    Environment: 'Dev'
  }
  sku: {
    name: 'Standard'
    capacity: 20
  }
  properties: {
    model: {
      format: 'OpenAI'
      name: 'gpt-4'
      version: '2024-12-17' // Using a more recent preview version (from gpt-4o-realtime-preview) as a proxy for 'gpt4.1'. Exact 'gpt4.1' model name is not directly available.
    }
  }
}

resource embeddingDeployment 'Microsoft.CognitiveServices/accounts/deployments@2023-05-01' = {
  parent: openAiAccount
  name: 'text-embedding-ada-002'
  tags: {
    Environment: 'Dev'
  }
  sku: {
    name: 'Standard'
    capacity: 20
  }
  properties: {
    model: {
      format: 'OpenAI'
      name: 'text-embedding-ada-002'
      version: '2'
    }
  }
}

output endpoint string = openAiAccount.properties.endpoint
@secure()
output apiKey string = listKeys(openAiAccount.id, '2023-05-01').key1
