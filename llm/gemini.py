"""
Google Gemini LLM wrapper for DeepResearch system.
"""

from typing import Dict, Any, List, Iterator
import google.generativeai as genai

from .base import LLMWrapper, LLMResponse


class GeminiWrapper(LLMWrapper):
    """Google Gemini LLM wrapper implementation."""
    
    def _get_provider_name(self) -> str:
        """Get the provider name."""
        return "gemini"
    
    def _initialize_client(self) -> genai.GenerativeModel:
        """Initialize Gemini client."""
        api_key = self.config.get('api_key')
        if not api_key:
            raise ValueError("Google API key is required")
        
        genai.configure(api_key=api_key)
        return genai.GenerativeModel(self.model)
    
    def _make_request(self, messages: List[Dict[str, str]], **kwargs) -> LLMResponse:
        """Make a request to Gemini API."""
        try:
            # Convert messages to Gemini format
            prompt = self._convert_messages_to_prompt(messages)
            
            # Configure generation parameters
            generation_config = genai.types.GenerationConfig(
                temperature=kwargs.get('temperature', self.temperature),
                max_output_tokens=kwargs.get('max_tokens', 8192),
            )
            
            # Make the request
            response = self.client.generate_content(
                prompt,
                generation_config=generation_config
            )
            
            # Extract response data
            content = response.text if response.text else ""
            
            # Gemini doesn't provide detailed usage stats in the same way
            usage = {
                'total_tokens': len(content.split()) * 1.3  # Rough estimate
            }
            
            metadata = {
                'finish_reason': 'stop',  # Gemini doesn't provide this directly
                'model': self.model
            }
            
            return LLMResponse(
                content=content,
                provider=self.provider,
                model=self.model,
                usage=usage,
                metadata=metadata
            )
            
        except Exception as e:
            self.log_error(f"Gemini API error: {e}")
            return LLMResponse(
                content="",
                provider=self.provider,
                model=self.model,
                error=f"API Error: {str(e)}"
            )
    
    def _make_streaming_request(
        self, 
        messages: List[Dict[str, str]], 
        **kwargs
    ) -> Iterator[str]:
        """Make a streaming request to Gemini API."""
        try:
            # Convert messages to Gemini format
            prompt = self._convert_messages_to_prompt(messages)
            
            # Configure generation parameters
            generation_config = genai.types.GenerationConfig(
                temperature=kwargs.get('temperature', self.temperature),
                max_output_tokens=kwargs.get('max_tokens', 8192),
            )
            
            # Make the streaming request
            response = self.client.generate_content(
                prompt,
                generation_config=generation_config,
                stream=True
            )
            
            for chunk in response:
                if chunk.text:
                    yield chunk.text
                    
        except Exception as e:
            self.log_error(f"Gemini streaming API error: {e}")
            yield f"Error: {str(e)}"
    
    def _convert_messages_to_prompt(self, messages: List[Dict[str, str]]) -> str:
        """Convert chat messages to a single prompt for Gemini."""
        prompt_parts = []
        
        for message in messages:
            role = message['role']
            content = message['content']
            
            if role == 'system':
                prompt_parts.append(f"System: {content}")
            elif role == 'user':
                prompt_parts.append(f"User: {content}")
            elif role == 'assistant':
                prompt_parts.append(f"Assistant: {content}")
        
        return "\n\n".join(prompt_parts)
    
    def validate_config(self) -> bool:
        """
        Validate Gemini configuration.
        
        Returns:
            True if configuration is valid
        """
        try:
            api_key = self.config.get('api_key')
            if not api_key:
                self.log_error("Google API key is missing")
                return False
            
            # Test API key by initializing client
            genai.configure(api_key=api_key)
            models = list(genai.list_models())
            
            self.log_info("Gemini configuration validated successfully")
            return True
            
        except Exception as e:
            self.log_error(f"Gemini configuration validation failed: {e}")
            return False 