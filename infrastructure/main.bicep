@description('Base name for all resources')
param baseName string = 'jarvis-assistant'

@description('Environment (dev, staging, prod)')
@allowed([
  'dev'
  'staging'
  'prod'
])
param environment string = 'dev'

@description('Azure region for all resources')
param location string = resourceGroup().location

@description('PostgreSQL admin username')
param postgresAdminUsername string = 'jarvisadmin'

@description('PostgreSQL admin password')
@secure()
param postgresAdminPassword string

@description('Enable Confidential Computing')
param enableConfidentialComputing bool = true

@description('Confidential Computing SKU')
@allowed([
  'DCsv2'
  'DCsv3'
])
param confidentialComputingSku string = 'DCsv3'

@description('Tenant Management Mode')
@allowed([
  'Shared'
  'Isolated'
])
param tenantManagementMode string = 'Shared'

@description('Admin username for Confidential Computing VMs')
param confidentialVmAdminUsername string = 'jarvisadmin'

@description('Cosmos DB account name')
param cosmosDbAccountName string = 'cosmos-${baseName}-${environment}'

@description('Cosmos DB database name')
param cosmosDbDatabaseName string = 'jarvis-db'

@description('Azure AI Service Configuration')
@allowed([
  'Standard'
  'Free'
])
param azureAIServiceTier string = 'Standard'

@description('Enable AI Shell Utilities')
param enableAIShellUtilities bool = true

var resourceTags = {
  Environment: environment
  Application: 'Jarvis Assistant'
  ManagedBy: 'Bicep'
  ArchitecturePattern: 'SaaS'
}

var nameSuffix = '${baseName}-${environment}'

// Virtual Network
resource virtualNetwork 'Microsoft.Network/virtualNetworks@2021-05-01' = {
  name: 'vnet-${nameSuffix}'
  location: location
  tags: resourceTags
  properties: {
    addressSpace: {
      addressPrefixes: [
        '10.0.0.0/16'
      ]
    }
    subnets: [
      {
        name: 'subnet-containers'
        properties: {
          addressPrefix: '10.0.1.0/24'
          privateEndpointNetworkPolicies: 'Disabled'
        }
      }
      {
        name: 'subnet-database'
        properties: {
          addressPrefix: '10.0.2.0/24'
          privateEndpointNetworkPolicies: 'Disabled'
        }
      }
    ]
  }
}

// Azure Container Registry
resource containerRegistry 'Microsoft.ContainerRegistry/registries@2021-12-01' = {
  name: 'acr${replace(nameSuffix, '-', '')}'
  location: location
  tags: resourceTags
  sku: {
    name: 'Standard'
  }
  properties: {
    adminUserEnabled: false
  }
}

// Azure Container Apps Environment
resource containerAppEnvironment 'Microsoft.App/managedEnvironments@2022-03-01' = {
  name: 'env-${nameSuffix}'
  location: location
  tags: resourceTags
  properties: {
    daprAIInstrumentationKey: applicationInsights.properties.InstrumentationKey
  }
}

// Azure Application Insights
resource applicationInsights 'Microsoft.Insights/components@2020-02-02' = {
  name: 'appi-${nameSuffix}'
  location: location
  tags: resourceTags
  kind: 'web'
  properties: {
    Application_Type: 'web'
    Flow_Type: 'Redfield'
    Request_Source: 'IbizaAIExtension'
  }
}

// Confidential Computing Managed Cluster
resource confidentialComputingCluster 'Microsoft.Compute/virtualMachineScaleSets@2023-03-01' = if (enableConfidentialComputing) {
  name: 'ccf-cluster-${nameSuffix}'
  location: location
  tags: resourceTags
  sku: {
    name: confidentialComputingSku
    tier: 'Standard'
    capacity: 2
  }
  properties: {
    orchestrationMode: 'Uniform'
    singlePlacementGroup: false
    platformFaultDomainCount: 1
    virtualMachineProfile: {
      osProfile: {
        computerNamePrefix: 'ccf'
        adminUsername: confidentialVmAdminUsername
        linuxConfiguration: {
          disablePasswordAuthentication: true
        }
      }
      storageProfile: {
        imageReference: {
          publisher: 'Canonical'
          offer: '0001-com-ubuntu-confidential-vm-focal'
          sku: '20_04-lts-cvm'
          version: 'latest'
        }
        osDisk: {
          createOption: 'FromImage'
          managedDisk: {
            storageAccountType: 'Premium_LRS'
            securityProfile: {
              securityEncryptionType: 'DiskWithVMGuestState'
            }
          }
        }
      }
      securityProfile: {
        uefiSettings: {
          secureBootEnabled: true
          vTpmEnabled: true
        }
        securityType: 'ConfidentialVM'
      }
    }
  }
}

// SaaS Tenant Management Resource
resource tenantManagementService 'Microsoft.SaaS/tenants@2022-01-01' = {
  name: 'tenant-mgmt-${nameSuffix}'
  location: location
  tags: resourceTags
  properties: {
    tenantMode: tenantManagementMode
    multiTenantEnabled: true
  }
}

// Azure Key Vault
resource keyVault 'Microsoft.KeyVault/vaults@2021-11-01-preview' = {
  name: 'kv-${nameSuffix}'
  location: location
  tags: resourceTags
  properties: {
    sku: {
      family: 'A'
      name: 'standard'
    }
    tenantId: subscription().tenantId
    enabledForDeployment: true
    enabledForDiskEncryption: true
    enabledForTemplateDeployment: true
    enableSoftDelete: true
    softDeleteRetentionInDays: 90
    accessPolicies: []
    networkAcls: {
      defaultAction: 'Deny'
      bypass: 'AzureServices'
      virtualNetworkRules: []
      ipRules: []
    }
  }
}

// Confidential Ledger for Immutable Logging
resource confidentialLedger 'Microsoft.ConfidentialLedger/ledgers@2022-05-13' = {
  name: 'ledger-${nameSuffix}'
  location: location
  tags: resourceTags
  properties: {
    ledgerType: 'Private'
    aadBasedSecurityPrincipals: []
  }
}

// Azure AD App Registration (placeholder for authentication)
resource adAppRegistration 'Microsoft.AAD/registeredApps@2021-04-01' = {
  name: 'app-${nameSuffix}'
  properties: {
    displayName: 'Jarvis Assistant SaaS App'
    signInAudience: 'AzureADMultipleOrgs'
  }
}

// Azure Cosmos DB Account
resource cosmosDbAccount 'Microsoft.DocumentDB/databaseAccounts@2023-04-15' = {
  name: cosmosDbAccountName
  location: location
  tags: resourceTags
  kind: 'GlobalDocumentDB'
  properties: {
    databaseAccountOfferType: 'Standard'
    enableAutomaticFailover: true
    enableMultipleWriteLocations: false
    consistencyPolicy: {
      defaultConsistencyLevel: 'Session'
    }
    locations: [
      {
        locationName: location
        failoverPriority: 0
        isZoneRedundant: false
      }
    ]
    capabilities: [
      {
        name: 'EnableServerless'
      }
      {
        name: 'EnableMongo'
      }
    ]
  }
}

// Cosmos DB Database
resource cosmosDbDatabase 'Microsoft.DocumentDB/databaseAccounts/sqlDatabases@2023-04-15' = {
  parent: cosmosDbAccount
  name: cosmosDbDatabaseName
  properties: {
    resource: {
      id: cosmosDbDatabaseName
    }
  }
}

// Azure AI Services
resource azureAIServices 'Microsoft.CognitiveServices/accounts@2023-05-01' = {
  name: 'ai-services-${nameSuffix}'
  location: location
  tags: resourceTags
  kind: 'AIServices'
  sku: {
    name: azureAIServiceTier
  }
  properties: {
    customSubDomainName: 'ai-services-${nameSuffix}'
    networkAcls: {
      defaultAction: 'Deny'
      bypass: 'AzureServices'
    }
  }
}

// AIShell Utilities Resource Group
resource aiShellResourceGroup 'Microsoft.Resources/resourceGroups@2021-04-01' = if (enableAIShellUtilities) {
  name: 'rg-aishell-${nameSuffix}'
  location: location
  tags: resourceTags
}

// AIShell Automation Account
resource aiShellAutomationAccount 'Microsoft.Automation/automationAccounts@2022-08-08' = if (enableAIShellUtilities) {
  name: 'aishell-automation-${nameSuffix}'
  location: location
  tags: resourceTags
  properties: {
    sku: {
      name: 'Basic'
    }
  }
  parent: aiShellResourceGroup
}

// Outputs for integration and reference
output containerRegistryLoginServer string = containerRegistry.properties.loginServer
output containerAppEnvironmentName string = containerAppEnvironment.name
output applicationInsightsInstrumentationKey string = applicationInsights.properties.InstrumentationKey
output keyVaultUri string = keyVault.properties.vaultUri
output adAppRegistrationId string = adAppRegistration.id
output confidentialComputingClusterId string = enableConfidentialComputing ? confidentialComputingCluster.id : ''
output tenantManagementServiceId string = tenantManagementService.id
output confidentialLedgerId string = confidentialLedger.id
output cosmosDbAccountEndpoint string = cosmosDbAccount.properties.documentEndpoint
output cosmosDbAccountId string = cosmosDbAccount.id
output azureAIServicesEndpoint string = azureAIServices.properties.endpoint
output azureAIServicesId string = azureAIServices.id
output aiShellAutomationAccountName string = enableAIShellUtilities ? aiShellAutomationAccount.name : ''
