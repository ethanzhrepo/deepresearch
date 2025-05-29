"""
Base LLM wrapper interface for DeepResearch system.
Provides unified interface for different LLM providers.
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional, AsyncIterator, Iterator
from dataclasses import dataclass
from enum import Enum

from utils.logger import LoggerMixin


class LLMProvider(Enum):
    """Supported LLM providers."""
    OPENAI = "openai"
    CLAUDE = "claude"
    GEMINI = "gemini"
    OLLAMA = "ollama"
    DEEPSEEK = "deepseek"


@dataclass
class LLMResponse:
    """Standard response format for LLM interactions."""
    content: str
    provider: str
    model: str
    usage: Optional[Dict[str, Any]] = None
    metadata: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    
    @property
    def is_success(self) -> bool:
        """Check if the response was successful."""
        return self.error is None
    
    @property
    def token_count(self) -> int:
        """Get total token count if available."""
        if self.usage:
            return self.usage.get('total_tokens', 0)
        return 0


class LLMWrapper(ABC, LoggerMixin):
    """
    Abstract base class for LLM wrappers.
    Provides unified interface for different LLM providers.
    """
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize LLM wrapper with configuration.
        
        Args:
            config: Provider-specific configuration
        """
        self.config = config
        self.provider = self._get_provider_name()
        self.model = config.get('model', 'default')
        self.temperature = config.get('temperature', 0.7)
        self._client = None
    
    @abstractmethod
    def _get_provider_name(self) -> str:
        """Get the provider name."""
        pass
    
    @abstractmethod
    def _initialize_client(self) -> Any:
        """Initialize the LLM client."""
        pass
    
    @abstractmethod
    def _make_request(self, messages: List[Dict[str, str]], **kwargs) -> LLMResponse:
        """Make a request to the LLM provider."""
        pass
    
    @abstractmethod
    def _make_streaming_request(
        self, 
        messages: List[Dict[str, str]], 
        **kwargs
    ) -> Iterator[str]:
        """Make a streaming request to the LLM provider."""
        pass
    
    @property
    def client(self):
        """Get or initialize the LLM client."""
        if self._client is None:
            self._client = self._initialize_client()
        return self._client
    
    def generate(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        max_tokens: Optional[int] = None,
        temperature: Optional[float] = None,
        **kwargs
    ) -> LLMResponse:
        """
        Generate response from prompt.
        
        Args:
            prompt: User prompt
            system_prompt: Optional system prompt
            max_tokens: Maximum tokens to generate
            temperature: Sampling temperature
            **kwargs: Additional provider-specific parameters
        
        Returns:
            LLMResponse object
        """
        try:
            messages = []
            
            if system_prompt:
                messages.append({"role": "system", "content": system_prompt})
            
            messages.append({"role": "user", "content": prompt})
            
            # Override default parameters
            request_kwargs = {
                "max_tokens": max_tokens,
                "temperature": temperature or self.temperature,
                **kwargs
            }
            
            # Remove None values
            request_kwargs = {k: v for k, v in request_kwargs.items() if v is not None}
            
            self.log_debug(f"Making request to {self.provider} with {len(messages)} messages")
            
            response = self._make_request(messages, **request_kwargs)
            
            if response.is_success:
                self.log_info(f"Successfully generated response ({response.token_count} tokens)")
            else:
                self.log_error(f"Request failed: {response.error}")
            
            return response
            
        except Exception as e:
            self.log_error(f"Error generating response", exception=e)
            return LLMResponse(
                content="",
                provider=self.provider,
                model=self.model,
                error=str(e)
            )
    
    def generate_streaming(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        max_tokens: Optional[int] = None,
        temperature: Optional[float] = None,
        **kwargs
    ) -> Iterator[str]:
        """
        Generate streaming response from prompt.
        
        Args:
            prompt: User prompt
            system_prompt: Optional system prompt
            max_tokens: Maximum tokens to generate
            temperature: Sampling temperature
            **kwargs: Additional provider-specific parameters
        
        Yields:
            Streaming response chunks
        """
        try:
            messages = []
            
            if system_prompt:
                messages.append({"role": "system", "content": system_prompt})
            
            messages.append({"role": "user", "content": prompt})
            
            # Override default parameters
            request_kwargs = {
                "max_tokens": max_tokens,
                "temperature": temperature or self.temperature,
                **kwargs
            }
            
            # Remove None values
            request_kwargs = {k: v for k, v in request_kwargs.items() if v is not None}
            
            self.log_debug(f"Making streaming request to {self.provider}")
            
            yield from self._make_streaming_request(messages, **request_kwargs)
            
        except Exception as e:
            self.log_error(f"Error in streaming generation", exception=e)
            yield f"Error: {str(e)}"
    
    def chat(
        self,
        messages: List[Dict[str, str]],
        max_tokens: Optional[int] = None,
        temperature: Optional[float] = None,
        **kwargs
    ) -> LLMResponse:
        """
        Chat with multiple messages.
        
        Args:
            messages: List of message dictionaries with 'role' and 'content'
            max_tokens: Maximum tokens to generate
            temperature: Sampling temperature
            **kwargs: Additional provider-specific parameters
        
        Returns:
            LLMResponse object
        """
        try:
            # Override default parameters
            request_kwargs = {
                "max_tokens": max_tokens,
                "temperature": temperature or self.temperature,
                **kwargs
            }
            
            # Remove None values
            request_kwargs = {k: v for k, v in request_kwargs.items() if v is not None}
            
            self.log_debug(f"Making chat request to {self.provider} with {len(messages)} messages")
            
            response = self._make_request(messages, **request_kwargs)
            
            if response.is_success:
                self.log_info(f"Successfully generated chat response ({response.token_count} tokens)")
            else:
                self.log_error(f"Chat request failed: {response.error}")
            
            return response
            
        except Exception as e:
            self.log_error(f"Error in chat", exception=e)
            return LLMResponse(
                content="",
                provider=self.provider,
                model=self.model,
                error=str(e)
            )
    
    def is_available(self) -> bool:
        """
        Check if the LLM provider is available.
        
        Returns:
            True if provider is available, False otherwise
        """
        try:
            # Try to initialize client
            client = self.client
            return client is not None
        except Exception as e:
            self.log_warning(f"Provider {self.provider} not available: {e}")
            return False
    
    def get_model_info(self) -> Dict[str, Any]:
        """
        Get information about the current model.
        
        Returns:
            Model information dictionary
        """
        return {
            "provider": self.provider,
            "model": self.model,
            "temperature": self.temperature,
            "available": self.is_available()
        }
    
    def _prepare_messages(self, messages: List[Dict[str, str]]) -> tuple:
        """
        Prepare messages for API call, handling provider-specific formats.
        
        Args:
            messages: List of message dictionaries
        
        Returns:
            Tuple of (processed_messages, system_message)
        """
        system_message = None
        processed_messages = []
        
        for msg in messages:
            if msg['role'] == 'system':
                # Some providers handle system messages separately
                if self._supports_system_message():
                    system_message = msg['content']
                else:
                    # Convert to user message for providers that don't support system role
                    processed_messages.append({
                        "role": "user", 
                        "content": f"System: {msg['content']}"
                    })
            else:
                processed_messages.append(msg)
        
        return processed_messages, system_message
    
    def _supports_system_message(self) -> bool:
        """
        Check if provider supports system messages natively.
        Override in subclasses if needed.
        """
        return True
    
    def _prepare_request_params(self, **kwargs) -> Dict[str, Any]:
        """
        Prepare request parameters, handling common parameter mapping.
        
        Args:
            **kwargs: Raw parameters
        
        Returns:
            Processed parameters for API call
        """
        params = {
            "model": self.model,
            "temperature": kwargs.get('temperature', self.temperature),
        }
        
        # Handle max_tokens parameter (different providers use different names)
        if 'max_tokens' in kwargs:
            max_tokens_key = self._get_max_tokens_param_name()
            params[max_tokens_key] = kwargs['max_tokens']
        
        # Add provider-specific parameters
        provider_params = self._get_provider_specific_params(**kwargs)
        params.update(provider_params)
        
        # Remove None values
        return {k: v for k, v in params.items() if v is not None}
    
    def _get_max_tokens_param_name(self) -> str:
        """
        Get the parameter name for max tokens for this provider.
        Override in subclasses if different from 'max_tokens'.
        """
        return "max_tokens"
    
    def _get_provider_specific_params(self, **kwargs) -> Dict[str, Any]:
        """
        Get provider-specific parameters.
        Override in subclasses to add custom parameters.
        """
        return {}
    
    def _extract_response_content(self, response: Any) -> str:
        """
        Extract content from API response.
        Must be implemented by subclasses.
        """
        raise NotImplementedError("Subclasses must implement _extract_response_content")
    
    def _extract_response_usage(self, response: Any) -> Optional[Dict[str, Any]]:
        """
        Extract usage information from API response.
        Override in subclasses if provider supports usage tracking.
        """
        return None
    
    def _extract_response_metadata(self, response: Any) -> Dict[str, Any]:
        """
        Extract metadata from API response.
        Override in subclasses to add provider-specific metadata.
        """
        return {}
    
    def _handle_api_error(self, error: Exception) -> str:
        """
        Handle API errors and return appropriate error message.
        Override in subclasses for provider-specific error handling.
        """
        return f"API Error: {str(error)}"
    
    def _make_request_with_retry(
        self, 
        messages: List[Dict[str, str]], 
        max_retries: int = 3,
        **kwargs
    ) -> LLMResponse:
        """
        Make request with automatic retry logic.
        
        Args:
            messages: Messages to send
            max_retries: Maximum number of retries
            **kwargs: Additional parameters
        
        Returns:
            LLMResponse object
        """
        last_error = None
        
        for attempt in range(max_retries + 1):
            try:
                return self._make_request(messages, **kwargs)
            except Exception as e:
                last_error = e
                if attempt < max_retries:
                    import time
                    wait_time = 2 ** attempt  # Exponential backoff
                    self.log_warning(f"Request failed (attempt {attempt + 1}), retrying in {wait_time}s: {e}")
                    time.sleep(wait_time)
                else:
                    self.log_error(f"Request failed after {max_retries + 1} attempts: {e}")
        
        # All retries failed
        return LLMResponse(
            content="",
            provider=self.provider,
            model=self.model,
            error=self._handle_api_error(last_error)
        ) 