from abc import ABC, abstractmethod
from typing import Optional, Dict, Any
import logging
from .exceptions import LLMError

logger = logging.getLogger(__name__)


class LLMProvider(ABC):
    """Abstract base class for LLM providers."""
    
    @abstractmethod
    def generate(self, system_prompt: str, user_prompt: str, image_data: Optional[str] = None) -> str:
        """
        Generate a response from the LLM.
        
        Args:
            system_prompt: The system prompt to guide the model
            user_prompt: The user's input/prompt
            image_data: Optional base64 encoded image for vision models
            
        Returns:
            The generated response as a string
        """
        pass


class OpenAIProvider(LLMProvider):
    """OpenAI implementation of the LLM provider."""
    
    def __init__(self, config: Dict[str, Any]):
        import openai
        import os
        api_key = config.get('key') or os.getenv('OPENAI_API_KEY')
        if not api_key:
            raise LLMError("OpenAI API key not found in config or environment")
        self.client = openai.OpenAI(api_key=api_key)
        self.model = config.get('model', 'gpt-4o-mini')
        self.vision_model = config.get('vision_model', 'gpt-4o')
    
    def generate(self, system_prompt: str, user_prompt: str, image_data: Optional[str] = None) -> str:
        """Generate response using OpenAI API."""
        messages = [
            {"role": "system", "content": system_prompt},
        ]
        
        if image_data:
            # Use vision model with image
            messages.append({
                "role": "user", 
                "content": [
                    {"type": "text", "text": user_prompt},
                    {"type": "image_url", "image_url": {"url": f"data:image/png;base64,{image_data}"}}
                ]
            })
            model = self.vision_model
        else:
            # Use regular model
            messages.append({"role": "user", "content": user_prompt})
            model = self.model
        
        try:
            response = self.client.chat.completions.create(
                model=model,
                messages=messages
            )
            content = response.choices[0].message.content
            if content is None:
                raise LLMError("OpenAI returned empty response")
            return content.strip()
        except openai.OpenAIError as e:
            logger.error(f"OpenAI API error: {e}")
            raise LLMError(f"OpenAI API error: {e}") from e
        except Exception as e:
            logger.error(f"Unexpected error in OpenAI API call: {e}")
            raise LLMError(f"Unexpected error in OpenAI API call: {e}") from e


class MockLLMProvider(LLMProvider):
    """Mock LLM provider for testing."""
    
    def __init__(self, responses: Optional[Dict[str, str]] = None):
        self.responses = responses or {}
        self.call_history = []
    
    def generate(self, system_prompt: str, user_prompt: str, image_data: Optional[str] = None) -> str:
        """Return mock response for testing."""
        # Record the call for verification
        call_info = {
            'system_prompt': system_prompt,
            'user_prompt': user_prompt,
            'image_data': image_data is not None
        }
        self.call_history.append(call_info)
        
        # Return predefined response or default
        key = f"{system_prompt[:50]}...{user_prompt[:50]}..."
        return self.responses.get(key, "Mock LLM response")
    
    def get_call_history(self):
        """Get history of all calls made to this provider."""
        return self.call_history


def create_llm_provider(config: Dict[str, Any]) -> LLMProvider:
    """
    Factory function to create the appropriate LLM provider based on config.
    
    Args:
        config: LLM configuration dictionary
        
    Returns:
        An instance of the appropriate LLMProvider
    """
    provider_type = config.get('provider', 'openai')
    
    if provider_type == 'openai':
        return OpenAIProvider(config)
    elif provider_type == 'mock':
        return MockLLMProvider(config.get('responses', {}))
    else:
        raise ValueError(f"Unsupported LLM provider: {provider_type}")
