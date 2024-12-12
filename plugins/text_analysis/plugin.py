from typing import Dict, Any
import spacy
from textblob import TextBlob
from transformers import pipeline
import logging
from ..plugin_manager import PluginBase

logger = logging.getLogger(__name__)


class TextAnalysisPlugin(PluginBase):
    """Plugin for advanced text analysis"""

    async def initialize(self) -> bool:
        try:
            # Load models
            self.nlp = spacy.load("en_core_web_sm")
            self.sentiment_analyzer = pipeline(
                "sentiment-analysis", model="distilbert-base-uncased-finetuned-sst-2-english"
            )
            return True
        except Exception as e:
            logger.error(f"Error initializing TextAnalysisPlugin: {e}")
            return False

    async def execute(self, **kwargs) -> Dict[str, Any]:
        """Execute text analysis"""
        try:
            text = kwargs.get("text", "")
            if not text:
                return {"error": "No text provided"}

            return {
                "spacy_analysis": await self._analyze_with_spacy(text),
                "sentiment_analysis": await self._analyze_sentiment(text),
                "textblob_analysis": await self._analyze_with_textblob(text),
            }
        except Exception as e:
            logger.error(f"Error executing TextAnalysisPlugin: {e}")
            return {"error": str(e)}

    async def cleanup(self) -> bool:
        """Cleanup resources"""
        try:
            # Clean up models if needed
            self.nlp = None
            self.sentiment_analyzer = None
            return True
        except Exception as e:
            logger.error(f"Error cleaning up TextAnalysisPlugin: {e}")
            return False

    async def _analyze_with_spacy(self, text: str) -> Dict[str, Any]:
        """Analyze text using spaCy"""
        doc = self.nlp(text)
        return {
            "entities": [
                {"text": ent.text, "label": ent.label_, "start": ent.start_char, "end": ent.end_char}
                for ent in doc.ents
            ],
            "noun_phrases": [chunk.text for chunk in doc.noun_chunks],
            "tokens": [
                {"text": token.text, "lemma": token.lemma_, "pos": token.pos_, "tag": token.tag_, "dep": token.dep_}
                for token in doc
            ],
        }

    async def _analyze_sentiment(self, text: str) -> Dict[str, Any]:
        """Analyze sentiment using Transformers"""
        result = self.sentiment_analyzer(text)[0]
        return {"label": result["label"], "score": float(result["score"])}

    async def _analyze_with_textblob(self, text: str) -> Dict[str, Any]:
        """Analyze text using TextBlob"""
        blob = TextBlob(text)
        return {
            "sentiment": {"polarity": blob.sentiment.polarity, "subjectivity": blob.sentiment.subjectivity},
            "language": blob.detect_language(),
            "tags": [(word, tag) for word, tag in blob.tags],
            "noun_phrases": list(blob.noun_phrases),
        }
