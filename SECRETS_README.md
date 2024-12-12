# Jarvis Assistant Secrets Management

## Prerequisites
- Azure CLI
- GitHub CLI
- Python 3.11+
- Poetry

## Obtaining Real Credentials

### 1. OpenAI API Key
1. Visit [OpenAI Platform](https://platform.openai.com/api-keys)
2. Click "Create new secret key"
3. Copy and save the key securely

### 2. Azure Credentials
```bash
# Login to Azure
az login

# Set your subscription (if you have multiple)
az account set --subscription "Your Subscription Name"

# Create service principal
az ad sp create-for-rbac --name "jarvis-assistant-sp" --role Contributor
```
Note down:
- `appId` (Client ID)
- `password` (Client Secret)
- `tenant` (Tenant ID)
- Your Subscription ID

### 3. Azure Container Registry
1. Create in Azure Portal
2. Note username and generate password

### 4. Database Connection String
For Azure PostgreSQL:
1. Create PostgreSQL Flexible Server
2. Get connection string format:
   ```
   postgresql://username:password@servername.postgres.database.azure.com/dbname?sslmode=require
   ```

### 5. Slack Webhook (Optional)
1. Go to [Slack API](https://api.slack.com/apps)
2. Create a new app
3. Add Incoming Webhook
4. Copy webhook URL

## Secret Generation Process

```bash
# Activate virtual environment
poetry shell

# Install dependencies
pip install cryptography python-jose

# Generate secrets interactively
python generate_secrets.py
```

## Setting GitHub Secrets

```bash
# Ensure GitHub CLI is authenticated
gh auth login

# Set secrets in GitHub repository
python setup_github_secrets.py "your-username/jarvis-assistant"
```

## Security Best Practices
⚠️ IMPORTANT:
- NEVER commit secrets to version control
- Treat `secrets` directory as highly sensitive
- Rotate secrets periodically
- Use environment-specific configurations
- Enable Azure AD Conditional Access
- Use Azure Key Vault for advanced secret management

## Troubleshooting
- Verify credentials before setting
- Check Azure RBAC permissions
- Ensure correct subscription context
- Validate connection strings

## Next Steps
1. Review generated secrets
2. Configure Azure resources
3. Set up additional environment configs
4. Implement secret rotation strategy
