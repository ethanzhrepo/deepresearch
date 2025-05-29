"""
DeepSeek LLM wrapper for DeepResearch system.
DeepSeek API is OpenAI-compatible with different base URL and models.
"""

from typing import Dict, Any, List, Iterator, Optional
import openai
from openai import OpenAI

from .base import LLMWrapper, LLMResponse


class DeepSeekWrapper(LLMWrapper):
    """DeepSeek LLM wrapper implementation using OpenAI-compatible API."""
    
    def _get_provider_name(self) -> str:
        """Get the provider name."""
        return "deepseek"
    
    def _initialize_client(self) -> OpenAI:
        """Initialize DeepSeek client using OpenAI library with custom base URL."""
        api_key = self.config.get('api_key')
        if not api_key:
            raise ValueError("DeepSeek API key is required")
        
        # DeepSeek uses OpenAI-compatible API with custom base URL
        return OpenAI(
            api_key=api_key,
            base_url="https://api.deepseek.com"
        )
    
    def _make_request(self, messages: List[Dict[str, str]], **kwargs) -> LLMResponse:
        """Make a request to DeepSeek API."""
        try:
            # Prepare request parameters using base class
            request_params = self._prepare_request_params(**kwargs)
            request_params["messages"] = messages  # DeepSeek handles system messages natively
            
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
            self.log_error(f"DeepSeek API error: {e}")
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
        """Extract content from DeepSeek API response."""
        return response.choices[0].message.content
    
    def _extract_response_usage(self, response: Any) -> Optional[Dict[str, Any]]:
        """Extract usage information from DeepSeek API response."""
        if response.usage:
            usage_data = {
                'prompt_tokens': response.usage.prompt_tokens,
                'completion_tokens': response.usage.completion_tokens,
                'total_tokens': response.usage.total_tokens
            }
            
            # DeepSeek-specific usage fields (if available)
            if hasattr(response.usage, 'prompt_cache_hit_tokens'):
                usage_data['prompt_cache_hit_tokens'] = response.usage.prompt_cache_hit_tokens
            if hasattr(response.usage, 'prompt_cache_miss_tokens'):
                usage_data['prompt_cache_miss_tokens'] = response.usage.prompt_cache_miss_tokens
                
            return usage_data
        return None
    
    def _extract_response_metadata(self, response: Any) -> Dict[str, Any]:
        """Extract metadata from DeepSeek API response."""
        metadata = {
            'finish_reason': response.choices[0].finish_reason,
            'response_id': response.id,
            'created': response.created
        }
        
        # DeepSeek-specific fields (if available)
        if hasattr(response, 'system_fingerprint'):
            metadata['system_fingerprint'] = response.system_fingerprint
            
        # DeepSeek reasoning content for deepseek-reasoner model
        if hasattr(response.choices[0].message, 'reasoning_content'):
            metadata['reasoning_content'] = response.choices[0].message.reasoning_content
            
        return metadata
    
    def _handle_api_error(self, error: Exception) -> str:
        """Handle DeepSeek-specific API errors."""
        if isinstance(error, openai.APIError):
            return f"DeepSeek API Error: {str(error)}"
        return super()._handle_api_error(error)
    
    def _make_streaming_request(
        self, 
        messages: List[Dict[str, str]], 
        **kwargs
    ) -> Iterator[str]:
        """Make a streaming request to DeepSeek API."""
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
            self.log_error(f"DeepSeek streaming API error: {e}")
            yield f"Error: {str(e)}"
        except Exception as e:
            self.log_error(f"Unexpected streaming error: {e}")
            yield f"Error: {str(e)}"
    
    def get_available_models(self) -> List[str]:
        """
        Get list of available DeepSeek models.
        
        Returns:
            List of model names
        """
        # DeepSeek models based on API documentation
        return [
            "deepseek-chat",      # Main chat model (DeepSeek-V3)
            "deepseek-reasoner",  # Reasoning model (DeepSeek-R1)
            "deepseek-coder"      # Code-focused model
        ]
    
    def estimate_tokens(self, text: str) -> int:
        """
        Estimate token count for text.
        Based on DeepSeek documentation: 1 English char ≈ 0.3 tokens, 1 Chinese char ≈ 0.6 tokens
        
        Args:
            text: Text to estimate tokens for
        
        Returns:
            Estimated token count
        """
        # Count Chinese and English characters separately
        chinese_chars = sum(1 for char in text if '\u4e00' <= char <= '\u9fff')
        other_chars = len(text) - chinese_chars
        
        # Apply DeepSeek's token estimation rules
        chinese_tokens = chinese_chars * 0.6
        english_tokens = other_chars * 0.3
        
        return int(chinese_tokens + english_tokens)
    
    def validate_config(self) -> bool:
        """
        Validate DeepSeek configuration.
        
        Returns:
            True if configuration is valid
        """
        try:
            api_key = self.config.get('api_key')
            if not api_key:
                self.log_error("DeepSeek API key is missing")
                return False
            
            # Test API key by making a simple request
            client = self._initialize_client()
            # Test with a minimal request
            response = client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": "Hello"}],
                max_tokens=1
            )
            
            self.log_info("DeepSeek configuration validated successfully")
            return True
            
        except Exception as e:
            self.log_error(f"DeepSeek configuration validation failed: {e}")
            return False
    
    def supports_function_calling(self) -> bool:
        """
        Check if the current model supports function calling.
        
        Returns:
            True if function calling is supported
        """
        # Based on DeepSeek documentation, function calling is supported
        return self.model in ["deepseek-chat"]
    
    def supports_json_output(self) -> bool:
        """
        Check if the current model supports JSON output mode.
        
        Returns:
            True if JSON output is supported
        """
        # Based on DeepSeek documentation, JSON output is supported
        return self.model in ["deepseek-chat", "deepseek-reasoner"] 