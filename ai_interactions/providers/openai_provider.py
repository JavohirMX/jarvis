"""
OpenAI provider implementation
Supports: GPT-4, GPT-3.5-turbo, GPT-4-turbo
"""
from typing import List, Optional, Generator
import openai
import tiktoken
from .base import BaseAIProvider, AIMessage, AIResponse


class OpenAIProvider(BaseAIProvider):
    """OpenAI API provider"""
    
    # Pricing per 1K tokens (as of 2024)
    PRICING = {
        'gpt-4': {'prompt': 0.03, 'completion': 0.06},
        'gpt-4-turbo': {'prompt': 0.01, 'completion': 0.03},
        'gpt-4-turbo-preview': {'prompt': 0.01, 'completion': 0.03},
        'gpt-3.5-turbo': {'prompt': 0.0005, 'completion': 0.0015},
        'gpt-3.5-turbo-16k': {'prompt': 0.001, 'completion': 0.002},
    }
    
    def __init__(self, api_key: str, model: str = None):
        super().__init__(api_key, model)
        openai.api_key = self.api_key
        self.client = openai.OpenAI(api_key=self.api_key)
    
    def get_default_model(self) -> str:
        return 'gpt-4-turbo-preview'
    
    def get_provider_name(self) -> str:
        return 'openai'
    
    def chat(
        self,
        messages: List[AIMessage],
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        **kwargs
    ) -> AIResponse:
        """Send chat request to OpenAI"""
        try:
            formatted_messages = self.prepare_messages(messages)
            
            response = self.client.chat.completions.create(
                model=self.model,
                messages=formatted_messages,
                temperature=temperature,
                max_tokens=max_tokens,
                **kwargs
            )
            
            usage = response.usage
            choice = response.choices[0]
            
            return AIResponse(
                content=choice.message.content,
                model=self.model,
                provider=self.get_provider_name(),
                prompt_tokens=usage.prompt_tokens,
                completion_tokens=usage.completion_tokens,
                total_tokens=usage.total_tokens,
                finish_reason=choice.finish_reason
            )
            
        except openai.OpenAIError as e:
            raise Exception(f"OpenAI API error: {str(e)}")
    
    def stream_chat(
        self,
        messages: List[AIMessage],
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        **kwargs
    ) -> Generator[str, None, None]:
        """Stream chat response from OpenAI"""
        try:
            formatted_messages = self.prepare_messages(messages)
            
            stream = self.client.chat.completions.create(
                model=self.model,
                messages=formatted_messages,
                temperature=temperature,
                max_tokens=max_tokens,
                stream=True,
                **kwargs
            )
            
            for chunk in stream:
                if chunk.choices[0].delta.content:
                    yield chunk.choices[0].delta.content
                    
        except openai.OpenAIError as e:
            raise Exception(f"OpenAI streaming error: {str(e)}")
    
    def count_tokens(self, text: str) -> int:
        """Count tokens using tiktoken"""
        try:
            encoding = tiktoken.encoding_for_model(self.model)
            return len(encoding.encode(text))
        except Exception:
            # Fallback to rough estimate
            return len(text.split()) * 1.3
    
    def estimate_cost(self, prompt_tokens: int, completion_tokens: int) -> float:
        """Calculate actual OpenAI costs"""
        pricing = self.PRICING.get(self.model, self.PRICING['gpt-4'])
        
        prompt_cost = (prompt_tokens / 1000) * pricing['prompt']
        completion_cost = (completion_tokens / 1000) * pricing['completion']
        
        return prompt_cost + completion_cost

