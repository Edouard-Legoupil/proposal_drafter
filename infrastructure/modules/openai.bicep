
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
  properties: {
    customSubDomainName: openAiAccountName
    publicNetworkAccess: 'Enabled'
  }
}

resource gpt4Deployment 'Microsoft.CognitiveServices/accounts/deployments@2023-05-01' = {
  parent: openAiAccount
  name: 'gpt-4'
  sku: {
    name: 'Standard'
    capacity: 20
  }
  properties: {
    model: {
      format: 'OpenAI'
      name: 'gpt-4'
      version: '1106-preview' // Using a recent, valid model version as a proxy for 'gpt-4.1'
    }
  }
}

resource embeddingDeployment 'Microsoft.CognitiveServices/accounts/deployments@2023-05-01' = {
  parent: openAiAccount
  name: 'text-embedding-ada-002'
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
