"""
OpenAI LLM wrapper for DeepResearch system.
"""

from typing import Dict, Any, List, Iterator, Optional
import openai
from openai import OpenAI

from .base import LLMWrapper, LLMResponse


class OpenAIWrapper(LLMWrapper):
    """OpenAI LLM wrapper implementation."""
    
    def _get_provider_name(self) -> str:
        """Get the provider name."""
        return "openai"
    
    def _initialize_client(self) -> OpenAI:
        """Initialize OpenAI client."""
        api_key = self.config.get('api_key')
        if not api_key:
            raise ValueError("OpenAI API key is required")
        
        return OpenAI(api_key=api_key)
    
    def _make_request(self, messages: List[Dict[str, str]], **kwargs) -> LLMResponse:
        """Make a request to OpenAI API."""
        try:
            # Prepare request parameters using base class
            request_params = self._prepare_request_params(**kwargs)
            request_params["messages"] = messages  # OpenAI handles system messages natively
            
            # Make the request
            response = self.client.chat.completions.create(**request_params)
            
            # Extract response data using helper methods
            content = self._extract_response_content(response)
            usage = self._extract_response_usage(response)
            metadata = self._extract_response_metadata(response)
            
            return LLMResponse(
                content=content,
                provider=self.provider,
                model=self.model,
                usage=usage,
                metadata=metadata
            )
            
        except openai.APIError as e:
            self.log_error(f"OpenAI API error: {e}")
            return LLMResponse(
                content="",
                provider=self.provider,
                model=self.model,
                error=self._handle_api_error(e)
            )
        except Exception as e:
            self.log_error(f"Unexpected error: {e}")
            return LLMResponse(
                content="",
                provider=self.provider,
                model=self.model,
                error=f"Unexpected error: {str(e)}"
            )
    
    def _extract_response_content(self, response: Any) -> str:
        """Extract content from OpenAI API response."""
        return response.choices[0].message.content
    
    def _extract_response_usage(self, response: Any) -> Optional[Dict[str, Any]]:
        """Extract usage information from OpenAI API response."""
        if response.usage:
            return {
                'prompt_tokens': response.usage.prompt_tokens,
                'completion_tokens': response.usage.completion_tokens,
                'total_tokens': response.usage.total_tokens
            }
        return None
    
    def _extract_response_metadata(self, response: Any) -> Dict[str, Any]:
        """Extract metadata from OpenAI API response."""
        return {
            'finish_reason': response.choices[0].finish_reason,
            'response_id': response.id,
            'created': response.created
        }
    
    def _handle_api_error(self, error: Exception) -> str:
        """Handle OpenAI-specific API errors."""
        if isinstance(error, openai.APIError):
            return f"OpenAI API Error: {str(error)}"
        return super()._handle_api_error(error)
    
    def _make_streaming_request(
        self, 
        messages: List[Dict[str, str]], 
        **kwargs
    ) -> Iterator[str]:
        """Make a streaming request to OpenAI API."""
        try:
            # Prepare request parameters
            request_params = {
                "model": self.model,
                "messages": messages,
                "temperature": kwargs.get('temperature', self.temperature),
                "stream": True
            }
            
            # Add optional parameters
            if 'max_tokens' in kwargs:
                request_params['max_tokens'] = kwargs['max_tokens']
            
            # Make the streaming request
            stream = self.client.chat.completions.create(**request_params)
            
            for chunk in stream:
                if chunk.choices[0].delta.content is not None:
                    yield chunk.choices[0].delta.content
                    
        except openai.APIError as e:
            self.log_error(f"OpenAI streaming API error: {e}")
            yield f"Error: {str(e)}"
        except Exception as e:
            self.log_error(f"Unexpected streaming error: {e}")
            yield f"Error: {str(e)}"
    
    def get_available_models(self) -> List[str]:
        """
        Get list of available OpenAI models.
        
        Returns:
            List of model names
        """
        try:
            models = self.client.models.list()
            return [model.id for model in models.data if 'gpt' in model.id]
        except Exception as e:
            self.log_error(f"Error fetching models: {e}")
            return []
    
    def estimate_tokens(self, text: str) -> int:
        """
        Estimate token count for text (rough approximation).
        
        Args:
            text: Text to estimate tokens for
        
        Returns:
            Estimated token count
        """
        # Rough approximation: 1 token ≈ 4 characters for English
        # For Chinese text, it's roughly 1 token per character
        chinese_chars = sum(1 for char in text if '\u4e00' <= char <= '\u9fff')
        other_chars = len(text) - chinese_chars
        
        return chinese_chars + (other_chars // 4)
    
    def validate_config(self) -> bool:
        """
        Validate OpenAI configuration.
        
        Returns:
            True if configuration is valid
        """
        try:
            api_key = self.config.get('api_key')
            if not api_key:
                self.log_error("OpenAI API key is missing")
                return False
            
            # Test API key by making a simple request
            client = self._initialize_client()
            models = client.models.list()
            
            self.log_info("OpenAI configuration validated successfully")
            return True
            
        except Exception as e:
            self.log_error(f"OpenAI configuration validation failed: {e}")
            return False 