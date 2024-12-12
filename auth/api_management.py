import asyncio
import logging
from typing import Dict, Any, Optional

from azure.identity import DefaultAzureCredential, ClientSecretCredential
from azure.apim.management import ApiManagementClient
from azure.mgmt.apimanagement import ApiManagementClient as AzureApiMgmtClient
import jwt
from cryptography.fernet import Fernet
import uuid
import hashlib
import os

class APIManagementService:
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize API Management Service
        
        Args:
            config (Dict[str, Any]): Configuration dictionary
        """
        self.config = config
        self.logger = logging.getLogger(self.__class__.__name__)
        
        # Azure Credentials
        self.credential = self._get_azure_credential()
        
        # API Management Clients
        self.apim_client = self._init_api_management_client()
        
        # Encryption Key Management
        self.encryption_key = self._generate_encryption_key()
        self.fernet = Fernet(self.encryption_key)

    def _get_azure_credential(self):
        """
        Get Azure Credential with fallback mechanisms
        
        Returns:
            Credential object for Azure authentication
        """
        try:
            # Try DefaultAzureCredential first
            return DefaultAzureCredential()
        except Exception as default_error:
            self.logger.warning(f"Default credential failed: {default_error}")
            
            # Fallback to ClientSecretCredential
            try:
                return ClientSecretCredential(
                    tenant_id=self.config.get('azure_tenant_id'),
                    client_id=self.config.get('azure_client_id'),
                    client_secret=self.config.get('azure_client_secret')
                )
            except Exception as client_secret_error:
                self.logger.error(f"All credential methods failed: {client_secret_error}")
                raise

    def _init_api_management_client(self):
        """
        Initialize Azure API Management Client
        
        Returns:
            Initialized API Management Client
        """
        try:
            subscription_id = self.config.get('azure_subscription_id')
            resource_group = self.config.get('resource_group')
            service_name = self.config.get('apim_service_name')
            
            return AzureApiMgmtClient(
                credential=self.credential,
                subscription_id=subscription_id
            )
        except Exception as e:
            self.logger.error(f"API Management Client initialization failed: {e}")
            return None

    def _generate_encryption_key(self) -> bytes:
        """
        Generate a secure encryption key
        
        Returns:
            Bytes representing the encryption key
        """
        return Fernet.generate_key()

    async def create_api_product(self, name: str, description: str):
        """
        Create a new API product in Azure API Management
        
        Args:
            name (str): Product name
            description (str): Product description
        
        Returns:
            Dict containing product details
        """
        try:
            product = await asyncio.to_thread(
                self.apim_client.product.create_or_update,
                resource_group_name=self.config.get('resource_group'),
                service_name=self.config.get('apim_service_name'),
                product_id=name.lower().replace(' ', '-'),
                parameters={
                    'display_name': name,
                    'description': description,
                    'subscription_required': True,
                    'approval_required': False,
                    'state': 'published'
                }
            )
            return {
                'id': product.id,
                'name': product.name,
                'description': product.description
            }
        except Exception as e:
            self.logger.error(f"API Product creation failed: {e}")
            return None

    def generate_jwt_token(self, user_id: str, roles: list = None) -> str:
        """
        Generate a JWT token for authentication
        
        Args:
            user_id (str): Unique user identifier
            roles (list, optional): User roles
        
        Returns:
            str: Signed JWT token
        """
        try:
            # Token payload
            payload = {
                'sub': user_id,
                'jti': str(uuid.uuid4()),
                'iat': int(asyncio.get_event_loop().time()),
                'exp': int(asyncio.get_event_loop().time()) + 3600,  # 1 hour expiration
                'roles': roles or ['user']
            }
            
            # Sign token with a secret key
            token = jwt.encode(
                payload, 
                self.config.get('jwt_secret_key'), 
                algorithm='HS256'
            )
            return token
        except Exception as e:
            self.logger.error(f"JWT token generation failed: {e}")
            return None

    def validate_jwt_token(self, token: str) -> Dict[str, Any]:
        """
        Validate and decode a JWT token
        
        Args:
            token (str): JWT token to validate
        
        Returns:
            Dict containing token payload or None if invalid
        """
        try:
            payload = jwt.decode(
                token, 
                self.config.get('jwt_secret_key'), 
                algorithms=['HS256']
            )
            return payload
        except jwt.ExpiredSignatureError:
            self.logger.warning("Token has expired")
        except jwt.InvalidTokenError:
            self.logger.warning("Invalid token")
        return None

    def encrypt_sensitive_data(self, data: str) -> str:
        """
        Encrypt sensitive data using Fernet symmetric encryption
        
        Args:
            data (str): Data to encrypt
        
        Returns:
            str: Encrypted data
        """
        try:
            return self.fernet.encrypt(data.encode()).decode()
        except Exception as e:
            self.logger.error(f"Data encryption failed: {e}")
            return None

    def decrypt_sensitive_data(self, encrypted_data: str) -> Optional[str]:
        """
        Decrypt sensitive data
        
        Args:
            encrypted_data (str): Encrypted data to decrypt
        
        Returns:
            Optional decrypted data
        """
        try:
            return self.fernet.decrypt(encrypted_data.encode()).decode()
        except Exception as e:
            self.logger.error(f"Data decryption failed: {e}")
            return None

    def generate_api_key(self, user_id: str) -> str:
        """
        Generate a secure API key
        
        Args:
            user_id (str): User identifier
        
        Returns:
            str: Generated API key
        """
        try:
            # Create a hash-based API key
            api_key_base = f"{user_id}:{asyncio.get_event_loop().time()}"
            api_key = hashlib.sha256(api_key_base.encode()).hexdigest()
            return api_key
        except Exception as e:
            self.logger.error(f"API key generation failed: {e}")
            return None

# Example usage and configuration
if __name__ == "__main__":
    import os
    from dotenv import load_dotenv

    load_dotenv()

    config = {
        'azure_tenant_id': os.getenv('AZURE_TENANT_ID'),
        'azure_client_id': os.getenv('AZURE_CLIENT_ID'),
        'azure_client_secret': os.getenv('AZURE_CLIENT_SECRET'),
        'azure_subscription_id': os.getenv('AZURE_SUBSCRIPTION_ID'),
        'resource_group': 'jarvis-assistant-rg',
        'apim_service_name': 'jarvis-api-management',
        'jwt_secret_key': os.getenv('JWT_SECRET_KEY', 'fallback_secret_key')
    }

    async def main():
        api_service = APIManagementService(config)
        
        # Create an API product
        product = await api_service.create_api_product(
            "Jarvis Core Services", 
            "Core API services for Jarvis Assistant"
        )
        print("API Product:", product)
        
        # Generate and validate JWT token
        user_id = "test_user_123"
        token = api_service.generate_jwt_token(user_id, ['admin'])
        print("Generated Token:", token)
        
        validated_payload = api_service.validate_jwt_token(token)
        print("Validated Payload:", validated_payload)
        
        # Encrypt and decrypt sensitive data
        sensitive_data = "Super secret information"
        encrypted = api_service.encrypt_sensitive_data(sensitive_data)
        decrypted = api_service.decrypt_sensitive_data(encrypted)
        print("Encrypted:", encrypted)
        print("Decrypted:", decrypted)

    asyncio.run(main())
