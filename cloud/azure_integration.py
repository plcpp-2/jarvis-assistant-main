from azure.identity import DefaultAzureCredential
from azure.storage.blob import BlobServiceClient
from azure.cosmos import CosmosClient
from azure.ai.textanalytics import TextAnalyticsClient
from azure.cognitiveservices.vision.computervision import ComputerVisionClient
from azure.core.credentials import AzureKeyCredential
from azure.keyvault.secrets import SecretClient
import logging
from typing import Optional, Dict, Any, List
import json

logger = logging.getLogger(__name__)

class AzureServices:
    def __init__(self, config: Dict[str, str]):
        self.config = config
        self.credential = DefaultAzureCredential()
        self.initialize_services()

    def initialize_services(self):
        """Initialize Azure services"""
        # Key Vault for secrets
        self.key_vault_client = SecretClient(
            vault_url=self.config['key_vault_url'],
            credential=self.credential
        )

        # Blob Storage
        self.blob_service = BlobServiceClient(
            account_url=self.config['storage_account_url'],
            credential=self.credential
        )

        # Cosmos DB
        self.cosmos_client = CosmosClient(
            url=self.config['cosmos_url'],
            credential=self.credential
        )

        # Cognitive Services
        self.text_analytics = TextAnalyticsClient(
            endpoint=self.config['cognitive_endpoint'],
            credential=self.credential
        )

        self.vision_client = ComputerVisionClient(
            endpoint=self.config['vision_endpoint'],
            credential=self.credential
        )

    async def get_secret(self, secret_name: str) -> Optional[str]:
        """Get secret from Key Vault"""
        try:
            secret = self.key_vault_client.get_secret(secret_name)
            return secret.value
        except Exception as e:
            logger.error(f"Error getting secret {secret_name}: {e}")
            return None

    async def store_blob(self, container: str, blob_name: str, data: bytes) -> bool:
        """Store data in Blob Storage"""
        try:
            container_client = self.blob_service.get_container_client(container)
            blob_client = container_client.get_blob_client(blob_name)
            blob_client.upload_blob(data, overwrite=True)
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
                'sentiment': sentiment_result[0].sentiment,
                'confidence_scores': sentiment_result[0].confidence_scores,
                'key_phrases': key_phrases_result[0].key_phrases,
                'entities': [{'text': entity.text, 'category': entity.category} 
                           for entity in entities_result[0].entities]
            }
        except Exception as e:
            logger.error(f"Error analyzing text: {e}")
            return {}

    async def analyze_image(self, image_url: str) -> Dict[str, Any]:
        """Analyze image using Azure Computer Vision"""
        try:
            analysis = self.vision_client.analyze_image(
                image_url,
                visual_features=['tags', 'description', 'objects', 'faces']
            )
            return {
                'description': analysis.description.captions[0].text,
                'tags': [tag.name for tag in analysis.tags],
                'objects': [obj.object_property for obj in analysis.objects],
                'faces': len(analysis.faces)
            }
        except Exception as e:
            logger.error(f"Error analyzing image: {e}")
            return {}
