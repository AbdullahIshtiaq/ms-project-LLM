import os
import json
import requests
from typing import List, Dict, Optional, Union
from dataclasses import dataclass

@dataclass
class LLMConfig:
    """Configuration for LLM models"""
    model_id: str
    api_key: str
    base_url: str = "https://openrouter.ai/api/v1"
    max_tokens: int = 1000
    temperature: float = 0.7
    top_p: float = 0.9

class OpenRouterClient:
    """Client for interacting with OpenRouter API"""
    
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.base_url = "https://openrouter.ai/api/v1"
        self.headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        }
        
        # Initialize model configurations
        self.models = {
            "gpt4_mini": LLMConfig(
                model_id="openai/gpt-4o-mini",
                api_key=api_key
            ),
            "gemini": LLMConfig(
                model_id="google/gemini-2.0-flash-exp:free",
                api_key=api_key
            ),
            "deepseek": LLMConfig(
                model_id="deepseek/deepseek-chat-v3-0324:free",
                api_key=api_key
            ),
            "llama4": LLMConfig(
                model_id="meta-llama/llama-4-maverick:free",
                api_key=api_key
            ),
        }

    def _make_request(
        self,
        model_config: LLMConfig,
        messages: List[Dict[str, str]],
        stream: bool = False,
        **kwargs
    ) -> Dict:
        """
        Make a request to the OpenRouter API
        
        Args:
            model_config: Configuration for the model to use
            messages: List of message dictionaries with 'role' and 'content'
            stream: Whether to stream the response
            **kwargs: Additional parameters to pass to the API
        
        Returns:
            Dict containing the API response
        """
        url = f"{self.base_url}/chat/completions"
        
        payload = {
            "model": model_config.model_id,
            "messages": messages,
            "stream": stream,
            "max_tokens": kwargs.get("max_tokens", model_config.max_tokens),
            "temperature": kwargs.get("temperature", model_config.temperature),
            "top_p": kwargs.get("top_p", model_config.top_p),
            **kwargs
        }
        
        try:
            response = requests.post(url, headers=self.headers, json=payload)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            raise Exception(f"Error making request to OpenRouter API: {str(e)}")

    def chat_completion(
        self,
        messages: List[Dict[str, str]],
        model_name: str = "gpt4_mini",
        stream: bool = False,
        **kwargs
    ) -> Dict:
        """
        Generate a chat completion using the specified model
        
        Args:
            messages: List of message dictionaries with 'role' and 'content'
            model_name: Name of the model to use (gpt4_mini, gemini, or deepseek)
            stream: Whether to stream the response
            **kwargs: Additional parameters to pass to the API
        
        Returns:
            Dict containing the API response
        """
        if model_name not in self.models:
            raise ValueError(f"Model {model_name} not found. Available models: {list(self.models.keys())}")
        
        return self._make_request(
            model_config=self.models[model_name],
            messages=messages,
            stream=stream,
            **kwargs
        )

    def get_available_models(self) -> List[Dict]:
        """
        Get list of available models from OpenRouter
        
        Returns:
            List of dictionaries containing model information
        """
        url = f"{self.base_url}/models"
        try:
            response = requests.get(url, headers=self.headers)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            raise Exception(f"Error fetching available models: {str(e)}")

# Example usage:
"""
# Initialize the client
client = OpenRouterClient(api_key="your-api-key")

# Example chat completion
messages = [
    {"role": "system", "content": "You are a helpful assistant."},
    {"role": "user", "content": "Hello, how are you?"}
]

# Using GPT-4 Mini
response = client.chat_completion(
    messages=messages,
    model_name="gpt4_mini",
    temperature=0.7
)

# Using Gemini
response = client.chat_completion(
    messages=messages,
    model_name="gemini",
    temperature=0.7
)

# Using DeepSeek
response = client.chat_completion(
    messages=messages,
    model_name="deepseek",
    temperature=0.7
)
""" 