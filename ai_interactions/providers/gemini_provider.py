"""
Google Gemini provider implementation
Supports: Gemini 2.5 Flash, Gemini 2.5 Pro, Gemini 1.5 Pro, Gemini 1.5 Flash
Reference: https://ai.google.dev/gemini-api/docs/text-generation
"""
from typing import List, Optional, Generator
try:
    from google import genai
    from google.genai import types
    GEMINI_AVAILABLE = True
except ImportError:
    GEMINI_AVAILABLE = False

from .base import BaseAIProvider, AIMessage, AIResponse


class GeminiProvider(BaseAIProvider):
    """Google Gemini API provider using the official google-genai SDK"""
    
    # Pricing per 1M tokens (as of 2025)
    # Source: https://ai.google.dev/pricing
    PRICING = {
        'gemini-2.5-flash': {'prompt': 0.075, 'completion': 0.30},
        'gemini-2.5-pro': {'prompt': 1.25, 'completion': 5.00},
        'gemini-1.5-pro': {'prompt': 1.25, 'completion': 5.00},
        'gemini-1.5-flash': {'prompt': 0.075, 'completion': 0.30},
        'gemini-pro': {'prompt': 0.50, 'completion': 1.50},  # Legacy
    }
    
    def __init__(self, api_key: str, model: str = None):
        if not GEMINI_AVAILABLE:
            raise ImportError(
                "google-genai package not installed. "
                "Run: pip install google-genai"
            )
        super().__init__(api_key, model)
        # Initialize client with API key
        self.client = genai.Client(api_key=self.api_key)
    
    def get_default_model(self) -> str:
        return 'gemini-2.5-flash'
    
    def get_provider_name(self) -> str:
        return 'gemini'
    
    def chat(
        self,
        messages: List[AIMessage],
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        **kwargs
    ) -> AIResponse:
        """
        Send chat request to Gemini (supports text and images)
        Reference: https://ai.google.dev/gemini-api/docs/text-generation
        Image support: https://ai.google.dev/gemini-api/docs/image-understanding
        """
        try:
            # Convert messages to Gemini format
            contents = []
            system_instruction = None
            
            for msg in messages:
                if msg.role == 'system':
                    # System instructions are separate in Gemini
                    system_instruction = msg.content
                else:
                    # Convert role: 'assistant' -> 'model' for Gemini
                    role = 'model' if msg.role == 'assistant' else msg.role
                    
                    # Build parts for this message (text + optional image)
                    parts = []
                    
                    # Add image first if present (Gemini best practice)
                    if msg.image_data and msg.image_mime_type:
                        # Determine upload strategy based on file size
                        image_size = len(msg.image_data)
                        
                        # Use inline data for files < 20MB, File API for larger files
                        if image_size < 20 * 1024 * 1024:  # 20MB threshold
                            # Inline base64 approach
                            parts.append(types.Part.from_bytes(
                                data=msg.image_data,
                                mime_type=msg.image_mime_type
                            ))
                        else:
                            # For large files, use File API
                            # Note: This requires uploading the file first
                            import tempfile
                            import os
                            
                            # Create temporary file
                            with tempfile.NamedTemporaryFile(delete=False, suffix='.img') as tmp_file:
                                tmp_file.write(msg.image_data)
                                tmp_path = tmp_file.name
                            
                            try:
                                # Upload file to Gemini
                                uploaded_file = self.client.files.upload(path=tmp_path)
                                # Use uploaded file reference
                                parts.append(types.Part.from_uri(
                                    file_uri=uploaded_file.uri,
                                    mime_type=msg.image_mime_type
                                ))
                            finally:
                                # Clean up temp file
                                if os.path.exists(tmp_path):
                                    os.unlink(tmp_path)
                    
                    # Add text content
                    parts.append({'text': msg.content})
                    
                    contents.append({
                        'role': role,
                        'parts': parts
                    })
            
            # Build generation config
            config_params = {
                'temperature': temperature,
            }
            if max_tokens:
                config_params['max_output_tokens'] = max_tokens
            
            # Disable thinking for 2.5 models (can be enabled via kwargs)
            if self.model.startswith('gemini-2.5'):
                config_params['thinking_config'] = types.ThinkingConfig(
                    thinking_budget=kwargs.get('thinking_budget', 0)
                )
            
            config = types.GenerateContentConfig(**config_params)
            
            # Generate content
            generate_params = {
                'model': self.model,
                'contents': contents,
                'config': config,
            }
            
            # if system_instruction:
            #     generate_params['system_instruction'] = system_instruction
            
            response = self.client.models.generate_content(**generate_params)
            
            # Extract usage metadata (if available)
            prompt_tokens = 0
            completion_tokens = 0
            
            if hasattr(response, 'usage_metadata'):
                usage = response.usage_metadata
                prompt_tokens = getattr(usage, 'prompt_token_count', 0)
                completion_tokens = getattr(usage, 'candidates_token_count', 0)
            
            # Fallback to estimation if usage not available
            if prompt_tokens == 0:
                prompt_tokens = self.count_tokens(' '.join([m.content for m in messages]))
            if completion_tokens == 0:
                completion_tokens = self.count_tokens(response.text)
            
            return AIResponse(
                content=response.text,
                model=self.model,
                provider=self.get_provider_name(),
                prompt_tokens=prompt_tokens,
                completion_tokens=completion_tokens,
                total_tokens=prompt_tokens + completion_tokens,
                finish_reason='stop'
            )
            
        except Exception as e:
            raise Exception(f"Gemini API error: {str(e)}")
    
    def stream_chat(
        self,
        messages: List[AIMessage],
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        **kwargs
    ) -> Generator[str, None, None]:
        """
        Stream chat response from Gemini (supports text and images)
        Reference: https://ai.google.dev/gemini-api/docs/text-generation#stream-response
        """
        try:
            # Convert messages to Gemini format
            contents = []
            system_instruction = None
            
            for msg in messages:
                if msg.role == 'system':
                    system_instruction = msg.content
                else:
                    role = 'model' if msg.role == 'assistant' else msg.role
                    
                    # Build parts for this message (text + optional image)
                    parts = []
                    
                    # Add image first if present
                    if msg.image_data and msg.image_mime_type:
                        # For streaming, use inline data only (simpler, faster)
                        parts.append(types.Part.from_bytes(
                            data=msg.image_data,
                            mime_type=msg.image_mime_type
                        ))
                    
                    # Add text content
                    parts.append({'text': msg.content})
                    
                    contents.append({
                        'role': role,
                        'parts': parts
                    })
            
            # Build generation config
            config_params = {
                'temperature': temperature,
            }
            if max_tokens:
                config_params['max_output_tokens'] = max_tokens
            
            # Disable thinking for streaming (faster)
            if self.model.startswith('gemini-2.5'):
                config_params['thinking_config'] = types.ThinkingConfig(
                    thinking_budget=0
                )
            
            config = types.GenerateContentConfig(**config_params)
            
            # Generate content with streaming
            generate_params = {
                'model': self.model,
                'contents': contents,
                'config': config,
            }
            
            # if system_instruction:
            #     generate_params['system_instruction'] = system_instruction
            
            response_stream = self.client.models.generate_content_stream(**generate_params)
            
            for chunk in response_stream:
                if chunk.text:
                    yield chunk.text
                    
        except Exception as e:
            raise Exception(f"Gemini streaming error: {str(e)}")
    
    def count_tokens(self, text: str) -> int:
        """
        Count tokens using Gemini's token counting API
        Falls back to estimation if API call fails
        """
        try:
            # Use official token counting API
            response = self.client.models.count_tokens(
                model=self.model,
                contents=text
            )
            return response.total_tokens
        except Exception:
            # Fallback to estimation: ~4 characters per token
            return len(text) // 4
    
    def estimate_cost(self, prompt_tokens: int, completion_tokens: int) -> float:
        """
        Calculate actual Gemini costs
        Pricing: https://ai.google.dev/pricing
        """
        pricing = self.PRICING.get(self.model, self.PRICING['gemini-2.5-flash'])
        
        prompt_cost = (prompt_tokens / 1_000_000) * pricing['prompt']
        completion_cost = (completion_tokens / 1_000_000) * pricing['completion']
        
        return prompt_cost + completion_cost

