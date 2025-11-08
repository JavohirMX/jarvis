"""
Abstract base class for AI providers
Following Strategy Pattern for easy provider switching
"""
from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Generator
from dataclasses import dataclass


@dataclass
class AIMessage:
    """Unified message format across all providers"""
    role: str  # 'system', 'user', 'assistant'
    content: str
    image_data: Optional[bytes] = None  # Image data for multimodal requests
    image_mime_type: Optional[str] = None  # MIME type (e.g., 'image/jpeg', 'image/png')


@dataclass
class AIResponse:
    """Unified response format across all providers"""
    content: str
    model: str
    provider: str
    prompt_tokens: int
    completion_tokens: int
    total_tokens: int
    finish_reason: str = 'stop'
    
    @property
    def estimated_cost(self) -> float:
        """Calculate estimated cost based on tokens and model"""
        # Override in subclasses for accurate pricing
        return (self.prompt_tokens * 0.00001) + (self.completion_tokens * 0.00003)


class BaseAIProvider(ABC):
    """
    Abstract base class for AI providers
    
    All AI providers (OpenAI, Anthropic, Gemini, etc.) must implement this interface
    """
    
    def __init__(self, api_key: str, model: str = None):
        """
        Initialize provider with API key and optional model
        
        Args:
            api_key: API key for the provider
            model: Model name (e.g., 'gpt-4', 'claude-3-opus', 'gemini-pro')
        """
        self.api_key = api_key
        self.model = model or self.get_default_model()
        self._validate_api_key()
    
    @abstractmethod
    def get_default_model(self) -> str:
        """Return the default model for this provider"""
        pass
    
    @abstractmethod
    def chat(
        self, 
        messages: List[AIMessage],
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        **kwargs
    ) -> AIResponse:
        """
        Send chat messages and get response
        
        Args:
            messages: List of AIMessage objects
            temperature: Sampling temperature (0-2)
            max_tokens: Maximum tokens in response
            **kwargs: Provider-specific parameters
            
        Returns:
            AIResponse object with unified format
        """
        pass
    
    @abstractmethod
    def stream_chat(
        self,
        messages: List[AIMessage],
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        **kwargs
    ) -> Generator[str, None, None]:
        """
        Stream chat response in real-time
        
        Args:
            messages: List of AIMessage objects
            temperature: Sampling temperature
            max_tokens: Maximum tokens in response
            **kwargs: Provider-specific parameters
            
        Yields:
            Content chunks as they arrive
        """
        pass
    
    @abstractmethod
    def count_tokens(self, text: str) -> int:
        """
        Count tokens in text using provider's tokenizer
        
        Args:
            text: Text to count tokens for
            
        Returns:
            Number of tokens
        """
        pass
    
    @abstractmethod
    def get_provider_name(self) -> str:
        """Return the provider name (e.g., 'openai', 'anthropic')"""
        pass
    
    def _validate_api_key(self):
        """Validate API key format"""
        if not self.api_key or len(self.api_key) < 10:
            raise ValueError(f"Invalid API key for {self.get_provider_name()}")
    
    def prepare_messages(self, messages: List[AIMessage]) -> List[Dict]:
        """
        Convert AIMessage objects to provider-specific format
        Override in subclass if provider uses different format
        
        Args:
            messages: List of AIMessage objects
            
        Returns:
            List of message dicts in provider format
        """
        return [{'role': msg.role, 'content': msg.content} for msg in messages]
    
    def estimate_cost(self, prompt_tokens: int, completion_tokens: int) -> float:
        """
        Estimate cost for given token usage
        Override in subclass for accurate provider pricing
        
        Args:
            prompt_tokens: Number of prompt tokens
            completion_tokens: Number of completion tokens
            
        Returns:
            Estimated cost in USD
        """
        # Default rough estimate (override in subclasses)
        return (prompt_tokens * 0.00001) + (completion_tokens * 0.00003)

