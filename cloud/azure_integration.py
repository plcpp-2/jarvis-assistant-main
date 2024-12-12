from azure.identity import (
    DefaultAzureCredential, 
    AzureCliCredential, 
    ClientSecretCredential,
    ManagedIdentityCredential,
    DeviceCodeCredential
)
from azure.storage.blob import BlobServiceClient
from azure.cosmos import CosmosClient
from azure.ai.textanalytics import TextAnalyticsClient
from azure.cognitiveservices.vision.computervision import ComputerVisionClient
from azure.core.credentials import AzureKeyCredential
from azure.keyvault.secrets import SecretClient
import logging
from typing import Optional, Dict, Any, List
import json
import os

logger = logging.getLogger(__name__)


class AzureServices:
    def __init__(self, config: Dict[str, str]):
        self.config = config
        self.credential = self._get_azure_credential()
        self.initialize_services()

    def _get_azure_credential(self):
        """
        Attempt multiple credential methods for Azure authentication
        Priority order:
        1. Managed Identity (for Azure resources)
        2. Azure CLI credentials
        3. Device Code credentials (interactive)
        4. Default Azure credentials
        5. Client secret credentials (from environment or config)
        """
        credential_methods = [
            self._try_managed_identity,
            self._try_azure_cli,
            self._try_device_code,
            self._try_default_credential,
            self._try_client_secret
        ]

        for method in credential_methods:
            try:
                return method()
            except Exception as error:
                logger.warning(f"{method.__name__} failed: {error}")
        
        raise ValueError("No valid Azure authentication method found")

    def _try_managed_identity(self):
        """Try Managed Identity authentication"""
        return ManagedIdentityCredential()

    def _try_azure_cli(self):
        """Try Azure CLI credentials"""
        return AzureCliCredential()

    def _try_device_code(self):
        """Try interactive device code authentication"""
        return DeviceCodeCredential(
            tenant_id=os.getenv('AZURE_TENANT_ID', self.config.get('TENANT_ID'))
        )

    def _try_default_credential(self):
        """Try default Azure credentials"""
        return DefaultAzureCredential()

    def _try_client_secret(self):
        """Try client secret credentials"""
        tenant_id = os.getenv('AZURE_TENANT_ID', self.config.get('TENANT_ID'))
        client_id = os.getenv('AZURE_CLIENT_ID', self.config.get('CLIENT_ID'))
        client_secret = os.getenv('AZURE_CLIENT_SECRET', self.config.get('CLIENT_SECRET'))
        
        if all([tenant_id, client_id, client_secret]):
            return ClientSecretCredential(
                tenant_id=tenant_id,
                client_id=client_id,
                client_secret=client_secret
            )
        raise ValueError("Insufficient client secret credentials")

    def initialize_services(self):
        """Initialize Azure services with robust error handling"""
        try:
            # Key Vault for secrets
            self.key_vault_client = SecretClient(vault_url=self.config["key_vault_url"], credential=self.credential)

            # Blob Storage
            self.blob_service = BlobServiceClient(
                account_url=self.config["storage_account_url"], credential=self.credential
            )

            # Cosmos DB
            self.cosmos_client = CosmosClient(url=self.config["cosmos_url"], credential=self.credential)

            # Cognitive Services
            self.text_analytics = TextAnalyticsClient(
                endpoint=self.config["cognitive_endpoint"], credential=self.credential
            )

            self.vision_client = ComputerVisionClient(endpoint=self.config["vision_endpoint"], credential=self.credential)
        
        except Exception as e:
            logger.error(f"Error initializing Azure services: {e}")
            raise

    async def get_secret(self, secret_name: str) -> Optional[str]:
        """Get secret from Key Vault with enhanced logging"""
        try:
            secret = self.key_vault_client.get_secret(secret_name)
            logger.info(f"Successfully retrieved secret: {secret_name}")
            return secret.value
        except Exception as e:
            logger.error(f"Error getting secret {secret_name}: {e}")
            return None

    async def store_blob(self, container: str, blob_name: str, data: bytes) -> bool:
        """Store data in Blob Storage with comprehensive error handling"""
        try:
            container_client = self.blob_service.get_container_client(container)
            blob_client = container_client.get_blob_client(blob_name)
            
            blob_client.upload_blob(data, overwrite=True)
            logger.info(f"Successfully uploaded blob: {blob_name} to container: {container}")
            return True
        except Exception as e:
            logger.error(f"Error storing blob {blob_name}: {e}")
            return False

    async def store_document(self, database: str, container: str, document: Dict) -> bool:
        """Store document in Cosmos DB"""
        try:
            database_client = self.cosmos_client.get_database_client(database)
            container_client = database_client.get_container_client(container)
            container_client.upsert_item(document)
            return True
        except Exception as e:
            logger.error(f"Error storing document: {e}")
            return False

    async def analyze_text(self, text: str) -> Dict[str, Any]:
        """Analyze text using Azure Cognitive Services"""
        try:
            documents = [text]
            sentiment_result = self.text_analytics.analyze_sentiment(documents)
            key_phrases_result = self.text_analytics.extract_key_phrases(documents)
            entities_result = self.text_analytics.recognize_entities(documents)

            return {
                "sentiment": sentiment_result[0].sentiment,
                "confidence_scores": sentiment_result[0].confidence_scores,
                "key_phrases": key_phrases_result[0].key_phrases,
                "entities": [
                    {"text": entity.text, "category": entity.category} for entity in entities_result[0].entities
                ],
            }
        except Exception as e:
            logger.error(f"Error analyzing text: {e}")
            return {}

    async def analyze_image(self, image_url: str) -> Dict[str, Any]:
        """Analyze image using Azure Computer Vision"""
        try:
            analysis = self.vision_client.analyze_image(
                image_url, visual_features=["tags", "description", "objects", "faces"]
            )
            return {
                "description": analysis.description.captions[0].text,
                "tags": [tag.name for tag in analysis.tags],
                "objects": [obj.object_property for obj in analysis.objects],
                "faces": len(analysis.faces),
            }
        except Exception as e:
            logger.error(f"Error analyzing image: {e}")
            return {}
