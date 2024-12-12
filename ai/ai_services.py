import asyncio
import logging
from typing import Dict, Any, Optional, List, Union

from azure.identity import DefaultAzureCredential
from azure.ai.textanalytics import TextAnalyticsClient
from azure.cognitiveservices.vision.computervision import ComputerVisionClient
from azure.core.credentials import AzureKeyCredential
import openai
import ollama

class AIServiceOrchestrator:
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize AI services with multi-provider support
        
        Args:
            config (Dict[str, Any]): Configuration dictionary for AI services
        """
        self.config = config
        self.logger = logging.getLogger(self.__class__.__name__)
        
        # Azure Credentials
        self.credential = DefaultAzureCredential()
        
        # Initialize AI Services
        self.text_analytics_client = self._init_text_analytics()
        self.computer_vision_client = self._init_computer_vision()
        
        # OpenAI and Ollama configurations
        self._configure_openai()
        self._configure_ollama()

    def _init_text_analytics(self) -> Optional[TextAnalyticsClient]:
        """Initialize Azure Text Analytics Client"""
        try:
            endpoint = self.config.get('azure_text_analytics_endpoint')
            key = self.config.get('azure_text_analytics_key')
            
            if not (endpoint and key):
                self.logger.warning("Azure Text Analytics credentials not found")
                return None
            
            return TextAnalyticsClient(endpoint, AzureKeyCredential(key))
        except Exception as e:
            self.logger.error(f"Text Analytics initialization failed: {e}")
            return None

    def _init_computer_vision(self) -> Optional[ComputerVisionClient]:
        """Initialize Azure Computer Vision Client"""
        try:
            endpoint = self.config.get('azure_computer_vision_endpoint')
            key = self.config.get('azure_computer_vision_key')
            
            if not (endpoint and key):
                self.logger.warning("Azure Computer Vision credentials not found")
                return None
            
            return ComputerVisionClient(endpoint, AzureKeyCredential(key))
        except Exception as e:
            self.logger.error(f"Computer Vision initialization failed: {e}")
            return None

    def _configure_openai(self):
        """Configure OpenAI client"""
        try:
            openai.api_key = self.config.get('openai_api_key')
            openai.organization = self.config.get('openai_org_id')
        except Exception as e:
            self.logger.error(f"OpenAI configuration failed: {e}")

    def _configure_ollama(self):
        """Configure local Ollama service"""
        try:
            ollama.init(
                host=self.config.get('ollama_host', 'localhost'),
                port=self.config.get('ollama_port', 11434)
            )
        except Exception as e:
            self.logger.error(f"Ollama configuration failed: {e}")

    async def analyze_text(self, text: str, language: str = 'en') -> Dict[str, Any]:
        """
        Perform multi-dimensional text analysis
        
        Args:
            text (str): Text to analyze
            language (str, optional): Language of the text. Defaults to 'en'.
        
        Returns:
            Dict[str, Any]: Analysis results
        """
        results = {}
        
        # Azure Text Analytics
        if self.text_analytics_client:
            try:
                sentiment_result = await self._async_sentiment_analysis(text, language)
                results['azure_sentiment'] = sentiment_result
            except Exception as e:
                self.logger.error(f"Azure text analysis failed: {e}")
        
        # OpenAI Analysis
        try:
            openai_analysis = await self._async_openai_text_analysis(text)
            results['openai_analysis'] = openai_analysis
        except Exception as e:
            self.logger.error(f"OpenAI text analysis failed: {e}")
        
        return results

    async def _async_sentiment_analysis(self, text: str, language: str):
        """Asynchronous sentiment analysis using Azure"""
        return await asyncio.to_thread(
            self.text_analytics_client.analyze_sentiment, 
            documents=[text], 
            language=language
        )

    async def _async_openai_text_analysis(self, text: str):
        """Asynchronous text analysis using OpenAI"""
        return await asyncio.to_thread(
            openai.ChatCompletion.create,
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "Analyze the sentiment, key entities, and provide insights."},
                {"role": "user", "content": text}
            ]
        )

    async def generate_response(self, prompt: str, model: str = 'llama2') -> str:
        """
        Generate AI response using multiple providers
        
        Args:
            prompt (str): Input prompt
            model (str, optional): Model to use. Defaults to 'llama2'.
        
        Returns:
            str: Generated response
        """
        try:
            # Try Ollama first
            ollama_response = await self._async_ollama_generate(prompt, model)
            return ollama_response
        except Exception as e:
            self.logger.warning(f"Ollama generation failed: {e}")
        
        try:
            # Fallback to OpenAI
            openai_response = await self._async_openai_generate(prompt)
            return openai_response
        except Exception as e:
            self.logger.error(f"All AI generation methods failed: {e}")
            return "I'm unable to generate a response at the moment."

    async def _async_ollama_generate(self, prompt: str, model: str):
        """Generate response using Ollama"""
        return await asyncio.to_thread(
            ollama.generate, 
            model=model, 
            prompt=prompt
        )

    async def _async_openai_generate(self, prompt: str):
        """Generate response using OpenAI"""
        response = await asyncio.to_thread(
            openai.ChatCompletion.create,
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are a helpful AI assistant."},
                {"role": "user", "content": prompt}
            ]
        )
        return response.choices[0].message.content

# Example usage and configuration
if __name__ == "__main__":
    import os
    from dotenv import load_dotenv

    load_dotenv()

    config = {
        'azure_text_analytics_endpoint': os.getenv('AZURE_TEXT_ANALYTICS_ENDPOINT'),
        'azure_text_analytics_key': os.getenv('AZURE_TEXT_ANALYTICS_KEY'),
        'azure_computer_vision_endpoint': os.getenv('AZURE_COMPUTER_VISION_ENDPOINT'),
        'azure_computer_vision_key': os.getenv('AZURE_COMPUTER_VISION_KEY'),
        'openai_api_key': os.getenv('OPENAI_API_KEY'),
        'openai_org_id': os.getenv('OPENAI_ORG_ID'),
        'ollama_host': 'localhost',
        'ollama_port': 11434
    }

    async def main():
        ai_service = AIServiceOrchestrator(config)
        
        # Text analysis example
        analysis = await ai_service.analyze_text("This is an amazing product!")
        print("Text Analysis:", analysis)
        
        # Response generation example
        response = await ai_service.generate_response("Tell me a joke about programming")
        print("AI Response:", response)

    asyncio.run(main())
