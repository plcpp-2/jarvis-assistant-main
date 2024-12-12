from typing import Dict, List, Optional, Any
import faiss
import numpy as np
from sentence_transformers import SentenceTransformer
import json
import logging
from pathlib import Path
from datetime import datetime
import pickle
from azure.storage.blob import BlobServiceClient
from azure.cognitiveservices.vision.computervision import ComputerVisionClient

logger = logging.getLogger(__name__)


class KnowledgeBase:
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.model = SentenceTransformer("all-MiniLM-L6-v2")
        self.index = None
        self.documents: List[Dict[str, Any]] = []
        self.initialize_index()

    def initialize_index(self):
        """Initialize FAISS index for semantic search"""
        embedding_size = self.model.get_sentence_embedding_dimension()
        self.index = faiss.IndexFlatL2(embedding_size)

    async def add_document(self, document: Dict[str, Any]):
        """Add a document to the knowledge base"""
        try:
            # Generate embedding
            text = self._prepare_text(document)
            embedding = self.model.encode([text])[0]

            # Add to FAISS index
            self.index.add(np.array([embedding], dtype=np.float32))

            # Store document
            document["timestamp"] = datetime.now().isoformat()
            document["embedding_id"] = len(self.documents)
            self.documents.append(document)

            return True
        except Exception as e:
            logger.error(f"Error adding document: {e}")
            return False

    async def search(self, query: str, k: int = 5) -> List[Dict[str, Any]]:
        """Search the knowledge base"""
        try:
            # Generate query embedding
            query_embedding = self.model.encode([query])[0]

            # Search FAISS index
            distances, indices = self.index.search(np.array([query_embedding], dtype=np.float32), k)

            # Return matched documents
            results = []
            for i, idx in enumerate(indices[0]):
                if idx < len(self.documents):
                    doc = self.documents[idx].copy()
                    doc["score"] = float(distances[0][i])
                    results.append(doc)

            return results
        except Exception as e:
            logger.error(f"Error searching knowledge base: {e}")
            return []

    def _prepare_text(self, document: Dict[str, Any]) -> str:
        """Prepare document text for embedding"""
        parts = [
            document.get("title", ""),
            document.get("content", ""),
            " ".join(document.get("tags", [])),
            document.get("summary", ""),
        ]
        return " ".join(filter(None, parts))

    async def save_to_disk(self, path: Path):
        """Save knowledge base to disk"""
        try:
            data = {"documents": self.documents, "index": faiss.serialize_index(self.index)}
            with open(path, "wb") as f:
                pickle.dump(data, f)
            return True
        except Exception as e:
            logger.error(f"Error saving knowledge base: {e}")
            return False

    async def load_from_disk(self, path: Path):
        """Load knowledge base from disk"""
        try:
            with open(path, "rb") as f:
                data = pickle.load(f)
            self.documents = data["documents"]
            self.index = faiss.deserialize_index(data["index"])
            return True
        except Exception as e:
            logger.error(f"Error loading knowledge base: {e}")
            return False


class EnhancedKnowledgeBase(KnowledgeBase):
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.blob_client = BlobServiceClient.from_connection_string(config["azure_storage_connection"])
        self.vision_client = ComputerVisionClient(config["vision_endpoint"], config["vision_credentials"])

    async def add_document_with_images(self, document: Dict[str, Any], images: List[str]):  # URLs or file paths
        """Add document with image analysis"""
        try:
            # Analyze images
            image_analyses = []
            for image_url in images:
                analysis = await self._analyze_image(image_url)
                if analysis:
                    image_analyses.append(analysis)

            # Add image analysis to document
            document["image_analyses"] = image_analyses

            # Add enhanced document
            return await self.add_document(document)
        except Exception as e:
            logger.error(f"Error adding document with images: {e}")
            return False

    async def _analyze_image(self, image_url: str) -> Optional[Dict[str, Any]]:
        """Analyze image using Azure Computer Vision"""
        try:
            analysis = self.vision_client.analyze_image(image_url, visual_features=["tags", "description", "objects"])
            return {
                "description": analysis.description.captions[0].text,
                "tags": [tag.name for tag in analysis.tags],
                "objects": [obj.object_property for obj in analysis.objects],
            }
        except Exception as e:
            logger.error(f"Error analyzing image: {e}")
            return None

    async def backup_to_azure(self, container_name: str):
        """Backup knowledge base to Azure Blob Storage"""
        try:
            container_client = self.blob_client.get_container_client(container_name)

            # Serialize knowledge base
            data = {"documents": self.documents, "index": faiss.serialize_index(self.index)}

            # Save to blob storage
            blob_name = f"knowledge_base_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pkl"
            blob_client = container_client.get_blob_client(blob_name)

            serialized_data = pickle.dumps(data)
            blob_client.upload_blob(serialized_data)

            return True
        except Exception as e:
            logger.error(f"Error backing up to Azure: {e}")
            return False

    async def restore_from_azure(self, container_name: str, blob_name: str):
        """Restore knowledge base from Azure Blob Storage"""
        try:
            container_client = self.blob_client.get_container_client(container_name)
            blob_client = container_client.get_blob_client(blob_name)

            # Download and deserialize
            downloaded_data = blob_client.download_blob().readall()
            data = pickle.loads(downloaded_data)

            # Restore knowledge base
            self.documents = data["documents"]
            self.index = faiss.deserialize_index(data["index"])

            return True
        except Exception as e:
            logger.error(f"Error restoring from Azure: {e}")
            return False
