"""
Anthropic Claude provider implementation
Supports: Claude 3 Opus, Claude 3 Sonnet, Claude 3 Haiku
"""
from typing import List, Optional, Generator
try:
    import anthropic
    ANTHROPIC_AVAILABLE = True
except ImportError:
    ANTHROPIC_AVAILABLE = False

from .base import BaseAIProvider, AIMessage, AIResponse


class AnthropicProvider(BaseAIProvider):
    """Anthropic Claude API provider"""
    
    # Pricing per 1M tokens (as of 2024)
    PRICING = {
        'claude-3-opus-20240229': {'prompt': 15.00, 'completion': 75.00},
        'claude-3-sonnet-20240229': {'prompt': 3.00, 'completion': 15.00},
        'claude-3-haiku-20240307': {'prompt': 0.25, 'completion': 1.25},
    }
    
    def __init__(self, api_key: str, model: str = None):
        if not ANTHROPIC_AVAILABLE:
            raise ImportError("anthropic package not installed. Run: pip install anthropic")
        super().__init__(api_key, model)
        self.client = anthropic.Anthropic(api_key=self.api_key)
    
    def get_default_model(self) -> str:
        return 'claude-3-sonnet-20240229'
    
    def get_provider_name(self) -> str:
        return 'anthropic'
    
    def chat(
        self,
        messages: List[AIMessage],
        temperature: float = 0.7,
        max_tokens: Optional[int] = 1024,
        **kwargs
    ) -> AIResponse:
        """Send chat request to Anthropic"""
        try:
            # Separate system message from other messages
            system_msg = None
            chat_messages = []
            
            for msg in messages:
                if msg.role == 'system':
                    system_msg = msg.content
                else:
                    chat_messages.append({'role': msg.role, 'content': msg.content})
            
            request_params = {
                'model': self.model,
                'messages': chat_messages,
                'max_tokens': max_tokens or 1024,
                'temperature': temperature,
                **kwargs
            }
            
            if system_msg:
                request_params['system'] = system_msg
            
            response = self.client.messages.create(**request_params)
            
            # Calculate tokens (Anthropic provides usage)
            prompt_tokens = response.usage.input_tokens
            completion_tokens = response.usage.output_tokens
            
            return AIResponse(
                content=response.content[0].text,
                model=self.model,
                provider=self.get_provider_name(),
                prompt_tokens=prompt_tokens,
                completion_tokens=completion_tokens,
                total_tokens=prompt_tokens + completion_tokens,
                finish_reason=response.stop_reason or 'stop'
            )
            
        except Exception as e:
            raise Exception(f"Anthropic API error: {str(e)}")
    
    def stream_chat(
        self,
        messages: List[AIMessage],
        temperature: float = 0.7,
        max_tokens: Optional[int] = 1024,
        **kwargs
    ) -> Generator[str, None, None]:
        """Stream chat response from Anthropic"""
        try:
            system_msg = None
            chat_messages = []
            
            for msg in messages:
                if msg.role == 'system':
                    system_msg = msg.content
                else:
                    chat_messages.append({'role': msg.role, 'content': msg.content})
            
            request_params = {
                'model': self.model,
                'messages': chat_messages,
                'max_tokens': max_tokens or 1024,
                'temperature': temperature,
                'stream': True,
                **kwargs
            }
            
            if system_msg:
                request_params['system'] = system_msg
            
            with self.client.messages.stream(**request_params) as stream:
                for text in stream.text_stream:
                    yield text
                    
        except Exception as e:
            raise Exception(f"Anthropic streaming error: {str(e)}")
    
    def count_tokens(self, text: str) -> int:
        """Estimate tokens (Anthropic uses similar tokenization to GPT)"""
        # Rough estimate: ~4 characters per token
        return len(text) // 4
    
    def estimate_cost(self, prompt_tokens: int, completion_tokens: int) -> float:
        """Calculate actual Anthropic costs"""
        pricing = self.PRICING.get(self.model, self.PRICING['claude-3-sonnet-20240229'])
        
        prompt_cost = (prompt_tokens / 1_000_000) * pricing['prompt']
        completion_cost = (completion_tokens / 1_000_000) * pricing['completion']
        
        return prompt_cost + completion_cost

