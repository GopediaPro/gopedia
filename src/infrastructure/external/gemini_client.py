"""
Gemini API Client for Embeddings and Summaries
"""
import os
from typing import Optional

import google.generativeai as genai
from src.services.ingestion_service import EmbeddingClient, Summarizer
from src.core.config import settings

class GeminiClient:
    """A wrapper for the Gemini API client."""
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or settings.LLM_API_KEY
        if not self.api_key:
            raise ValueError("Gemini API key is required. Set LLM_API_KEY in .env file.")
        
        genai.configure(api_key=self.api_key)

class GeminiEmbeddingClient(GeminiClient, EmbeddingClient):
    """Gemini client for text embeddings."""
    
    async def embed_text(
        self,
        text: str,
        *,
        model: str,
        dimensions: Optional[int] = None,
        max_retries: int = 2,
    ) -> list[float]:
        """
        Embed text using Gemini API.
        
        Args:
            text: The text to embed.
            model: The embedding model to use.
            dimensions: The target dimension for the embedding (optional).
            max_retries: The maximum number of retries (not implemented for simplicity).
            
        Returns:
            A list of floats representing the embedding.
        """
        try:
            # Gemini API uses output_dimensionality instead of dimensions
            result = genai.embed_content(
                model=model,
                content=text,
                task_type="retrieval_document",
                output_dimensionality=dimensions
            )
            return result["embedding"]
        except Exception as e:
            print(f"Error embedding text with Gemini: {e}")
            # In a real implementation, you would add retry logic here.
            raise

class GeminiSummarizer(GeminiClient, Summarizer):
    """Gemini client for text summarization."""
    
    def __init__(
        self,
        api_key: Optional[str] = None,
        generation_model: str = settings.LLM_GENERATION_MODEL
    ):
        super().__init__(api_key)
        self.model = genai.GenerativeModel(generation_model)

    async def summarize(
        self,
        text: str,
        *,
        context: Optional[str] = None,
        max_retries: int = 2
    ) -> str:
        """
        Summarize text using Gemini API.
        
        Args:
            text: The text to summarize.
            context: Optional context for the summary.
            max_retries: The maximum number of retries (not implemented for simplicity).
            
        Returns:
            A string containing the summary.
        """
        prompt_parts = []
        if context:
            prompt_parts.append(f"Context: {context}")
        
        prompt_parts.append(f"Please summarize the following text:\n\n{text}")
        
        prompt = "\n\n".join(prompt_parts)
        
        try:
            response = self.model.generate_content(prompt)
            return response.text
        except Exception as e:
            print(f"Error summarizing text with Gemini: {e}")
            # In a real implementation, you would add retry logic here.
            raise
