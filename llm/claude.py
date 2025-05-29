"""
Anthropic Claude LLM wrapper for DeepResearch system.
"""

from typing import Dict, Any, List, Iterator, Optional
import anthropic

from .base import LLMWrapper, LLMResponse


class ClaudeWrapper(LLMWrapper):
    """Anthropic Claude LLM wrapper implementation."""
    
    def _get_provider_name(self) -> str:
        """Get the provider name."""
        return "claude"
    
    def _initialize_client(self) -> anthropic.Anthropic:
        """Initialize Anthropic client."""
        api_key = self.config.get('api_key')
        if not api_key:
            raise ValueError("Anthropic API key is required")
        
        return anthropic.Anthropic(api_key=api_key)
    
    def _make_request(self, messages: List[Dict[str, str]], **kwargs) -> LLMResponse:
        """Make a request to Anthropic API."""
        try:
            # Use base class message preparation
            processed_messages, system_message = self._prepare_messages(messages)
            
            # Prepare request parameters using base class
            request_params = self._prepare_request_params(**kwargs)
            request_params["messages"] = processed_messages
            
            if system_message:
                request_params['system'] = system_message
            
            # Make the request
            response = self.client.messages.create(**request_params)
            
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
            
        except anthropic.APIError as e:
            self.log_error(f"Claude API error: {e}")
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
        """Extract content from Claude API response."""
        return response.content[0].text if response.content else ""
    
    def _extract_response_usage(self, response: Any) -> Optional[Dict[str, Any]]:
        """Extract usage information from Claude API response."""
        if response.usage:
            return {
                'prompt_tokens': response.usage.input_tokens,
                'completion_tokens': response.usage.output_tokens,
                'total_tokens': response.usage.input_tokens + response.usage.output_tokens
            }
        return None
    
    def _extract_response_metadata(self, response: Any) -> Dict[str, Any]:
        """Extract metadata from Claude API response."""
        return {
            'stop_reason': response.stop_reason,
            'response_id': response.id,
            'model': response.model
        }
    
    def _handle_api_error(self, error: Exception) -> str:
        """Handle Claude-specific API errors."""
        if isinstance(error, anthropic.APIError):
            return f"Claude API Error: {str(error)}"
        return super()._handle_api_error(error)
    
    def _make_streaming_request(
        self, 
        messages: List[Dict[str, str]], 
        **kwargs
    ) -> Iterator[str]:
        """Make a streaming request to Anthropic API."""
        try:
            # Convert messages format for Claude
            system_message = None
            claude_messages = []
            
            for msg in messages:
                if msg['role'] == 'system':
                    system_message = msg['content']
                else:
                    claude_messages.append(msg)
            
            # Prepare request parameters
            request_params = {
                "model": self.model,
                "messages": claude_messages,
                "temperature": kwargs.get('temperature', self.temperature),
                "max_tokens": kwargs.get('max_tokens', 4000),
                "stream": True
            }
            
            if system_message:
                request_params['system'] = system_message
            
            # Make the streaming request
            with self.client.messages.stream(**request_params) as stream:
                for text in stream.text_stream:
                    yield text
                    
        except anthropic.APIError as e:
            self.log_error(f"Claude streaming API error: {e}")
            yield f"Error: {str(e)}"
        except Exception as e:
            self.log_error(f"Unexpected streaming error: {e}")
            yield f"Error: {str(e)}"
    
    def validate_config(self) -> bool:
        """
        Validate Claude configuration.
        
        Returns:
            True if configuration is valid
        """
        try:
            api_key = self.config.get('api_key')
            if not api_key:
                self.log_error("Anthropic API key is missing")
                return False
            
            # Test API key by initializing client
            client = self._initialize_client()
            
            self.log_info("Claude configuration validated successfully")
            return True
            
        except Exception as e:
            self.log_error(f"Claude configuration validation failed: {e}")
            return False