
// modules/postgres.bicep
@description('The location for the PostgreSQL server.')
param location string

@description('The prefix for the PostgreSQL server name.')
param prefix string

@description('The size of the environment.')
param environmentSize string

@secure()
param adminPassword string = newGuid()

var postgresServerName = '${prefix}-postgres-${uniqueString(resourceGroup().id)}'
var postgresDatabaseName = 'proposalgen_db'

var skus = {
  Testing: {
    name: 'Standard_B1ms'
    tier: 'Burstable'
  }
  Exploratory: {
    name: 'Standard_B1ms'
    tier: 'Burstable'
  }
  Expanded: {
    name: 'Standard_D2s_v3'
    tier: 'GeneralPurpose'
  }
  'Organization-Wide': {
    name: 'Standard_D4s_v3'
    tier: 'GeneralPurpose'
  }
}

resource postgresServer 'Microsoft.DBforPostgreSQL/flexibleServers@2022-01-20-preview' = {
  name: postgresServerName
  location: location
  sku: skus[environmentSize]
  tags: {
    Environment: 'Dev'
  }
  properties: {
    administratorLogin: 'psqladmin'
    administratorLoginPassword: adminPassword
    version: '14'
    storage: {
      storageSizeGB: 32
    }
    backup: {
      backupRetentionDays: 7
      geoRedundantBackup: 'Disabled'
    }
    network: {
      publicNetworkAccess: 'Enabled' // For simplicity in this example
    }
  }
}

resource postgresDatabase 'Microsoft.DBforPostgreSQL/flexibleServers/databases@2022-01-20-preview' = {
  parent: postgresServer
  name: postgresDatabaseName
  tags: {
    Environment: 'Dev'
  }
}

// Enable pgvector extension
resource pgvectorExtension 'Microsoft.DBforPostgreSQL/flexibleServers/configurations@2022-01-20-preview' = {
  parent: postgresServer
  name: 'azure.extensions'
  properties: {
    value: 'VECTOR'
  }
}


output serverName string = postgresServer.name
output databaseName string = postgresDatabase.name
output adminUser string = postgresServer.properties.administratorLogin
@secure()
output adminPassword string = adminPassword
