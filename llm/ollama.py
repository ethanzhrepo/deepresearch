"""
Ollama local LLM wrapper for DeepResearch system.
"""

from typing import Dict, Any, List, Iterator, Optional
import requests
import json

from .base import LLMWrapper, LLMResponse


class OllamaWrapper(LLMWrapper):
    """Ollama local LLM wrapper implementation."""
    
    def _get_provider_name(self) -> str:
        """Get the provider name."""
        return "ollama"
    
    def _initialize_client(self) -> str:
        """Initialize Ollama client (returns base URL)."""
        base_url = self.config.get('base_url', 'http://localhost:11434')
        
        # Test connection
        try:
            response = requests.get(f"{base_url}/api/tags", timeout=5)
            response.raise_for_status()
            return base_url
        except Exception as e:
            raise ValueError(f"Cannot connect to Ollama server at {base_url}: {e}")
    
    def _supports_system_message(self) -> bool:
        """Ollama doesn't support system messages natively."""
        return False
    
    def _get_max_tokens_param_name(self) -> str:
        """Ollama uses 'num_predict' instead of 'max_tokens'."""
        return "num_predict"
    
    def _get_provider_specific_params(self, **kwargs) -> Dict[str, Any]:
        """Get Ollama-specific parameters."""
        params = {}
        
        # Ollama uses 'options' for model parameters
        options = {}
        
        if 'temperature' in kwargs:
            options['temperature'] = kwargs['temperature']
        
        if 'num_predict' in kwargs:
            options['num_predict'] = kwargs['num_predict']
        
        if options:
            params['options'] = options
        
        # Ollama-specific parameters
        params['stream'] = kwargs.get('stream', False)
        
        return params
    
    def _make_request(self, messages: List[Dict[str, str]], **kwargs) -> LLMResponse:
        """Make a request to Ollama API."""
        try:
            # Convert messages to prompt (Ollama doesn't use chat format)
            prompt = self._convert_messages_to_prompt(messages)
            
            # Prepare request data
            data = {
                "model": self.model,
                "prompt": prompt,
                "stream": False,
            }
            
            # Add provider-specific parameters
            provider_params = self._get_provider_specific_params(**kwargs)
            data.update(provider_params)
            
            # Make the request
            response = requests.post(
                f"{self.client}/api/generate",
                json=data,
                timeout=120
            )
            response.raise_for_status()
            
            result = response.json()
            
            # Extract response data using helper methods
            content = self._extract_response_content(result)
            usage = self._extract_response_usage(result)
            metadata = self._extract_response_metadata(result)
            
            return LLMResponse(
                content=content,
                provider=self.provider,
                model=self.model,
                usage=usage,
                metadata=metadata
            )
            
        except requests.RequestException as e:
            self.log_error(f"Ollama API request error: {e}")
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
        """Extract content from Ollama API response."""
        return response.get('response', '')
    
    def _extract_response_usage(self, response: Any) -> Optional[Dict[str, Any]]:
        """Extract usage information from Ollama API response."""
        return {
            'prompt_eval_count': response.get('prompt_eval_count', 0),
            'eval_count': response.get('eval_count', 0),
            'total_tokens': response.get('prompt_eval_count', 0) + response.get('eval_count', 0)
        }
    
    def _extract_response_metadata(self, response: Any) -> Dict[str, Any]:
        """Extract metadata from Ollama API response."""
        return {
            'model': response.get('model', self.model),
            'done': response.get('done', True),
            'total_duration': response.get('total_duration', 0),
            'load_duration': response.get('load_duration', 0),
            'prompt_eval_duration': response.get('prompt_eval_duration', 0),
            'eval_duration': response.get('eval_duration', 0)
        }
    
    def _handle_api_error(self, error: Exception) -> str:
        """Handle Ollama-specific API errors."""
        if isinstance(error, requests.RequestException):
            return f"Ollama Request Error: {str(error)}"
        return super()._handle_api_error(error)
    
    def _make_streaming_request(
        self, 
        messages: List[Dict[str, str]], 
        **kwargs
    ) -> Iterator[str]:
        """Make a streaming request to Ollama API."""
        try:
            # Convert messages to prompt
            prompt = self._convert_messages_to_prompt(messages)
            
            # Prepare request data
            data = {
                "model": self.model,
                "prompt": prompt,
                "stream": True,
                "options": {
                    "temperature": kwargs.get('temperature', self.temperature),
                }
            }
            
            if 'max_tokens' in kwargs:
                data["options"]["num_predict"] = kwargs['max_tokens']
            
            # Make the streaming request
            response = requests.post(
                f"{self.client}/api/generate",
                json=data,
                stream=True,
                timeout=120
            )
            response.raise_for_status()
            
            for line in response.iter_lines():
                if line:
                    try:
                        chunk = json.loads(line.decode('utf-8'))
                        if 'response' in chunk:
                            yield chunk['response']
                        if chunk.get('done', False):
                            break
                    except json.JSONDecodeError:
                        continue
                        
        except requests.RequestException as e:
            self.log_error(f"Ollama streaming API error: {e}")
            yield f"Error: {str(e)}"
        except Exception as e:
            self.log_error(f"Unexpected streaming error: {e}")
            yield f"Error: {str(e)}"
    
    def _convert_messages_to_prompt(self, messages: List[Dict[str, str]]) -> str:
        """Convert chat messages to a single prompt for Ollama."""
        prompt_parts = []
        
        for message in messages:
            role = message['role']
            content = message['content']
            
            if role == 'system':
                prompt_parts.append(f"System: {content}")
            elif role == 'user':
                prompt_parts.append(f"Human: {content}")
            elif role == 'assistant':
                prompt_parts.append(f"Assistant: {content}")
        
        # Add final prompt for assistant response
        prompt_parts.append("Assistant:")
        
        return "\n\n".join(prompt_parts)
    
    def get_available_models(self) -> List[str]:
        """
        Get list of available Ollama models.
        
        Returns:
            List of model names
        """
        try:
            response = requests.get(f"{self.client}/api/tags", timeout=10)
            response.raise_for_status()
            
            data = response.json()
            return [model['name'] for model in data.get('models', [])]
            
        except Exception as e:
            self.log_error(f"Error fetching Ollama models: {e}")
            return []
    
    def pull_model(self, model_name: str) -> bool:
        """
        Pull a model to Ollama.
        
        Args:
            model_name: Name of the model to pull
        
        Returns:
            True if successful
        """
        try:
            data = {"name": model_name}
            response = requests.post(
                f"{self.client}/api/pull",
                json=data,
                timeout=300  # 5 minutes timeout for model download
            )
            response.raise_for_status()
            
            self.log_info(f"Successfully pulled model: {model_name}")
            return True
            
        except Exception as e:
            self.log_error(f"Error pulling model {model_name}: {e}")
            return False
    
    def validate_config(self) -> bool:
        """
        Validate Ollama configuration.
        
        Returns:
            True if configuration is valid
        """
        try:
            base_url = self.config.get('base_url', 'http://localhost:11434')
            
            # Test connection
            response = requests.get(f"{base_url}/api/tags", timeout=5)
            response.raise_for_status()
            
            # Check if model exists
            data = response.json()
            available_models = [model['name'] for model in data.get('models', [])]
            
            if self.model not in available_models:
                self.log_warning(f"Model {self.model} not found in Ollama. Available models: {available_models}")
                return False
            
            self.log_info("Ollama configuration validated successfully")
            return True
            
        except Exception as e:
            self.log_error(f"Ollama configuration validation failed: {e}")
            return False 