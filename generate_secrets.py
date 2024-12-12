import os
import secrets
import base64
import uuid
import json
import getpass
from cryptography.fernet import Fernet
from jose import jwt

def get_user_input(prompt, default=None, secure=False):
    """Prompt user for input with optional default and secure input."""
    if default:
        prompt += f" (default: {default})"
    prompt += ": "
    
    if secure:
        value = getpass.getpass(prompt)
    else:
        value = input(prompt)
    
    return value.strip() or default

def generate_secret(length=32):
    """Generate a cryptographically secure random secret."""
    return secrets.token_hex(length)

def generate_jwt_secret():
    """Generate a secure JWT secret."""
    return secrets.token_urlsafe(32)

def main():
    secrets_dir = os.path.join(os.path.dirname(__file__), 'secrets')
    os.makedirs(secrets_dir, exist_ok=True)

    # Interactive secret input
    secrets_config = {
        "OPENAI_API_KEY": get_user_input("Enter OpenAI API Key", secure=True),
        
        "AZURE_CREDENTIALS": {
            "clientId": get_user_input("Enter Azure Client ID"),
            "clientSecret": get_user_input("Enter Azure Client Secret", secure=True),
            "subscriptionId": get_user_input("Enter Azure Subscription ID"),
            "tenantId": get_user_input("Enter Azure Tenant ID")
        },
        
        "ACR_USERNAME": get_user_input("Enter Azure Container Registry Username", "jarviscontainerregistry"),
        "ACR_PASSWORD": get_user_input("Enter Azure Container Registry Password", secure=True),
        
        "DATABASE_CONNECTION_STRING": get_user_input("Enter Database Connection String"),
        
        "JWT_SECRET": generate_jwt_secret(),
        
        "SLACK_WEBHOOK": get_user_input("Enter Slack Webhook URL (optional)", default="")
    }

    # Save as JSON
    with open(os.path.join(secrets_dir, 'github_secrets.json'), 'w') as f:
        json.dump(secrets_config, f, indent=2)

    # Create environment variable file
    env_content = "\n".join([
        f"{key}={value}" if not isinstance(value, dict) else 
        "\n".join([f"{key}_{k}={v}" for k, v in value.items()])
        for key, value in secrets_config.items()
    ])
    
    with open(os.path.join(secrets_dir, '.env'), 'w') as f:
        f.write(env_content)

    print("\n🔐 Secrets generated successfully in 'secrets' directory.")
    print("IMPORTANT: Keep these secrets confidential and do not commit them to version control!")

if __name__ == "__main__":
    main()
