
// modules/redis.bicep
@description('The location for the Redis cache.')
param location string

@description('The prefix for the Redis cache name.')
param prefix string

@description('The size of the environment.')
param environmentSize string

var redisCacheName = '${prefix}-redis-${uniqueString(resourceGroup().id)}'

var skus = {
  Testing: {
    name: 'Basic'
    family: 'C'
    capacity: 0
  }
  Exploratory: {
    name: 'Basic'
    family: 'C'
    capacity: 0
  }
  Expanded: {
    name: 'Standard'
    family: 'C'
    capacity: 1
  }
  'Organization-Wide': {
    name: 'Standard'
    family: 'C'
    capacity: 1
  }
}

resource redisCache 'Microsoft.Cache/Redis@2022-06-01' = {
  name: redisCacheName
  location: location
  sku: skus[environmentSize]
  tags: {
    Environment: 'Dev'
  }
  properties: {
    enableNonSslPort: false
    publicNetworkAccess: 'Enabled' // For simplicity in this example
  }
}

output hostName string = redisCache.properties.hostName
output port int = redisCache.properties.sslPort
@secure()
output password string = redisCache.listKeys().primaryKey
