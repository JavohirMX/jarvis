"""
Factory for creating AI providers
Implements Factory Pattern for easy provider instantiation
"""
from typing import Optional
from django.conf import settings
from .base import BaseAIProvider
from .openai_provider import OpenAIProvider
from .anthropic_provider import AnthropicProvider
from .gemini_provider import GeminiProvider


class AIProviderFactory:
    """Factory for creating AI provider instances"""
    
    PROVIDERS = {
        'openai': OpenAIProvider,
        'anthropic': AnthropicProvider,
        'gemini': GeminiProvider,
    }
    
    @classmethod
    def create(
        cls,
        provider_name: str,
        api_key: Optional[str] = None,
        model: Optional[str] = None
    ) -> BaseAIProvider:
        """
        Create an AI provider instance
        
        Args:
            provider_name: Provider name ('openai', 'anthropic', 'gemini')
            api_key: API key (uses settings if not provided)
            model: Model name (uses provider default if not provided)
            
        Returns:
            BaseAIProvider instance
            
        Raises:
            ValueError: If provider is not supported
        """
        provider_name = provider_name.lower()
        
        if provider_name not in cls.PROVIDERS:
            available = ', '.join(cls.PROVIDERS.keys())
            raise ValueError(
                f"Provider '{provider_name}' not supported. "
                f"Available providers: {available}"
            )
        
        # Get API key from settings if not provided
        if not api_key:
            api_key = cls._get_api_key_from_settings(provider_name)
        
        provider_class = cls.PROVIDERS[provider_name]
        return provider_class(api_key=api_key, model=model)
    
    @classmethod
    def _get_api_key_from_settings(cls, provider_name: str) -> str:
        """Get API key from Django settings"""
        key_map = {
            'openai': 'OPENAI_API_KEY',
            'anthropic': 'ANTHROPIC_API_KEY',
            'gemini': 'GEMINI_API_KEY',
        }
        
        setting_name = key_map.get(provider_name)
        if not setting_name:
            raise ValueError(f"No API key setting for provider: {provider_name}")
        
        api_key = getattr(settings, setting_name, None)
        if not api_key:
            raise ValueError(
                f"{setting_name} not found in settings. "
                f"Please add it to your .env file"
            )
        
        return api_key
    
    @classmethod
    def get_default_provider(cls) -> BaseAIProvider:
        """Get the default provider from settings"""
        default_provider = getattr(settings, 'DEFAULT_AI_PROVIDER', 'openai')
        return cls.create(default_provider)
    
    @classmethod
    def register_provider(cls, name: str, provider_class: type):
        """
        Register a custom provider
        
        Args:
            name: Provider name
            provider_class: Provider class (must inherit from BaseAIProvider)
        """
        if not issubclass(provider_class, BaseAIProvider):
            raise ValueError("Provider must inherit from BaseAIProvider")
        
        cls.PROVIDERS[name.lower()] = provider_class


# Convenience function
def get_ai_provider(
    provider_name: Optional[str] = None,
    api_key: Optional[str] = None,
    model: Optional[str] = None
) -> BaseAIProvider:
    """
    Get an AI provider instance
    
    Args:
        provider_name: Provider name (uses default if not provided)
        api_key: API key (uses settings if not provided)
        model: Model name (uses provider default if not provided)
        
    Returns:
        BaseAIProvider instance
    """
    if provider_name:
        return AIProviderFactory.create(provider_name, api_key, model)
    return AIProviderFactory.get_default_provider()

