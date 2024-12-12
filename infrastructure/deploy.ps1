param (
    [string]$ResourceGroupName = "jarvis-assistant-rg",
    [string]$Location = "eastus",
    [string]$Environment = "dev"
)

# Ensure you're logged in to Azure
az login

# Create resource group if it doesn't exist
$rgExists = az group exists --name $ResourceGroupName
if ($rgExists -eq "false") {
    az group create --name $ResourceGroupName --location $Location
}

# Generate a secure PostgreSQL admin password
$postgresPassword = -join ((48..57) + (65..90) + (97..122) | Get-Random -Count 16 | ForEach-Object {[char]$_})

# Deploy Bicep template
az deployment group create `
    --resource-group $ResourceGroupName `
    --template-file main.bicep `
    --parameters main.parameters.json `
    --parameters environment=$Environment postgresAdminPassword=$postgresPassword

Write-Host "Deployment completed successfully!" -ForegroundColor Green
Write-Host "Resource Group: $ResourceGroupName" -ForegroundColor Cyan
Write-Host "Environment: $Environment" -ForegroundColor Cyan
