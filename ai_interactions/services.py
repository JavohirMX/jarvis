"""
AI Service Layer
High-level interface for AI operations using multiple providers
"""
from typing import List, Dict, Optional, Generator
from django.contrib.auth.models import User
from .models import AIMemory
from .providers import get_ai_provider
from .providers.base import AIMessage as ProviderMessage, AIResponse


class AIService:
    """
    Service layer for AI operations
    Handles provider selection, context building, and response processing
    """
    
    def __init__(
        self,
        user: User,
        provider: str = None,
        model: str = None
    ):
        """
        Initialize AI service for a user
        
        Args:
            user: Django user instance
            provider: AI provider name ('openai', 'anthropic', 'gemini')
            model: Specific model to use
        """
        self.user = user
        self.provider = get_ai_provider(provider, model=model)
        self.memory, _ = AIMemory.objects.get_or_create(user=user)
    
    def chat(
        self,
        message: str,
        context: Optional[Dict] = None,
        conversation_history: Optional[List[Dict]] = None,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        image_data: Optional[bytes] = None,
        image_mime_type: Optional[str] = None
    ) -> AIResponse:
        """
        Send a chat message and get AI response
        
        Args:
            message: User message
            context: Optional context (clipboard, active_app, etc.)
            conversation_history: Previous messages in conversation
            temperature: Sampling temperature
            max_tokens: Maximum tokens in response
            image_data: Optional image data for multimodal requests
            image_mime_type: MIME type of the image (e.g., 'image/jpeg')
            
        Returns:
            AIResponse with content and token usage
        """
        messages = self._build_messages(
            message, context, conversation_history, 
            image_data, image_mime_type
        )
        return self.provider.chat(
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens
        )
    
    def stream_chat(
        self,
        message: str,
        context: Optional[Dict] = None,
        conversation_history: Optional[List[Dict]] = None,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        image_data: Optional[bytes] = None,
        image_mime_type: Optional[str] = None
    ) -> Generator[str, None, None]:
        """
        Stream chat response in real-time
        
        Args:
            message: User message
            context: Optional context
            conversation_history: Previous messages
            temperature: Sampling temperature
            max_tokens: Maximum tokens in response
            image_data: Optional image data for multimodal requests
            image_mime_type: MIME type of the image
            
        Yields:
            Response chunks as they arrive
        """
        messages = self._build_messages(
            message, context, conversation_history,
            image_data, image_mime_type
        )
        yield from self.provider.stream_chat(
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens
        )
    
    def summarize(
        self,
        text: str,
        length: str = 'medium'
    ) -> AIResponse:
        """
        Summarize text
        
        Args:
            text: Text to summarize
            length: Desired length ('short', 'medium', 'long')
            
        Returns:
            AIResponse with summary
        """
        length_instructions = {
            'short': 'in 1-2 sentences',
            'medium': 'in a paragraph',
            'long': 'in detail with key points'
        }
        
        instruction = length_instructions.get(length, 'concisely')
        
        messages = [
            ProviderMessage(
                role='system',
                content=f'You are a helpful assistant that summarizes text {instruction}.'
            ),
            ProviderMessage(
                role='user',
                content=f'Please summarize the following text:\n\n{text}'
            )
        ]
        
        return self.provider.chat(messages=messages, temperature=0.3)
    
    def translate(
        self,
        text: str,
        target_language: str
    ) -> AIResponse:
        """
        Translate text to target language
        
        Args:
            text: Text to translate
            target_language: Target language (e.g., 'Spanish', 'French')
            
        Returns:
            AIResponse with translation
        """
        messages = [
            ProviderMessage(
                role='system',
                content=f'You are a professional translator. Translate the following text to {target_language}.'
            ),
            ProviderMessage(
                role='user',
                content=text
            )
        ]
        
        return self.provider.chat(messages=messages, temperature=0.3)
    
    def explain_code(
        self,
        code: str,
        language: Optional[str] = None
    ) -> AIResponse:
        """
        Explain code snippet
        
        Args:
            code: Code to explain
            language: Programming language (optional)
            
        Returns:
            AIResponse with explanation
        """
        lang_prefix = f'{language} ' if language else ''
        
        messages = [
            ProviderMessage(
                role='system',
                content='You are an expert programmer. Explain code clearly and concisely.'
            ),
            ProviderMessage(
                role='user',
                content=f'Please explain this {lang_prefix}code:\n\n```\n{code}\n```'
            )
        ]
        
        return self.provider.chat(messages=messages, temperature=0.5)
    
    def _build_messages(
        self,
        user_message: str,
        context: Optional[Dict] = None,
        conversation_history: Optional[List[Dict]] = None,
        image_data: Optional[bytes] = None,
        image_mime_type: Optional[str] = None
    ) -> List[ProviderMessage]:
        """
        Build message list with system prompt, history, and context
        
        Args:
            user_message: Current user message
            context: Optional context dictionary
            conversation_history: Previous messages
            image_data: Optional image data for current message
            image_mime_type: MIME type of the image
            
        Returns:
            List of ProviderMessage objects
        """
        messages = []
        
        # System message with user memory and context
        system_content = self._build_system_prompt(context)
        messages.append(ProviderMessage(role='system', content=system_content))
        
        # Add conversation history (without re-sending old images)
        if conversation_history:
            for msg in conversation_history[-10:]:  # Last 10 messages for context
                messages.append(ProviderMessage(
                    role=msg['role'],
                    content=msg['content']
                ))
        
        # Add current message (with optional image)
        messages.append(ProviderMessage(
            role='user',
            content=user_message,
            image_data=image_data,
            image_mime_type=image_mime_type
        ))
        
        return messages
    
    def _build_system_prompt(self, context: Optional[Dict] = None) -> str:
        """
        Build system prompt with user memory and context
        
        Args:
            context: Optional context dictionary
            
        Returns:
            System prompt string
        """
        prompt_parts = [
            "You are Jarvis, a helpful AI assistant for a desktop application.",
        ]
        
        # Add user memory/preferences
        if self.memory and self.memory.key_facts:
            facts = self.memory.key_facts
            if facts:
                prompt_parts.append(f"\nUser information: {facts}")
        
        # Add context if provided
        if context:
            if context.get('clipboard'):
                prompt_parts.append(f"\nClipboard content: {context['clipboard']}")
            if context.get('active_app'):
                prompt_parts.append(f"\nActive application: {context['active_app']}")
        
        # Add response length preference
        if hasattr(self.user, 'profile'):
            length = self.user.profile.ai_response_length
            if length == 'short':
                prompt_parts.append("\nKeep responses brief and concise.")
            elif length == 'long':
                prompt_parts.append("\nProvide detailed and comprehensive responses.")
        
        return '\n'.join(prompt_parts)
    
    def count_tokens(self, text: str) -> int:
        """
        Count tokens in text
        
        Args:
            text: Text to count tokens for
            
        Returns:
            Number of tokens
        """
        return self.provider.count_tokens(text)
    
    def estimate_cost(self, prompt_tokens: int, completion_tokens: int) -> float:
        """
        Estimate cost for token usage
        
        Args:
            prompt_tokens: Number of prompt tokens
            completion_tokens: Number of completion tokens
            
        Returns:
            Estimated cost in USD
        """
        return self.provider.estimate_cost(prompt_tokens, completion_tokens)

