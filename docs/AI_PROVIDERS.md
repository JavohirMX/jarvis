# AI Provider Architecture

## Overview

The AI Assistant supports multiple AI providers through a clean, extensible architecture using the **Strategy Pattern**. This allows you to:

- Switch between providers (OpenAI, Anthropic, Gemini)
- Use different models per request
- Add new providers easily
- A/B test providers
- Fallback to alternatives if one fails

## Supported Providers

### 1. OpenAI
**Models:** GPT-4, GPT-4-Turbo, GPT-3.5-Turbo  
**Best for:** General chat, code, reasoning  
**Pricing:** $0.03-$0.06 per 1K tokens

### 2. Anthropic (Claude)
**Models:** Claude 3 Opus, Sonnet, Haiku  
**Best for:** Long context, analysis, writing  
**Pricing:** $0.25-$75 per 1M tokens

### 3. Google Gemini
**Models:** Gemini 2.5 Flash, Gemini 2.5 Pro, Gemini 1.5 Pro, Gemini 1.5 Flash  
**Best for:** Fast responses, cost-effective, thinking mode  
**Pricing:** $0.075-$5.00 per 1M tokens  
**Docs:** https://ai.google.dev/gemini-api/docs/text-generation

## Configuration

### 1. Environment Variables

Add to your `.env` file:

```bash
# Choose default provider
DEFAULT_AI_PROVIDER=openai  # Options: openai, anthropic, gemini
DEFAULT_AI_MODEL=  # Leave empty for provider default

# API Keys (add the ones you'll use)
OPENAI_API_KEY=sk-...
ANTHROPIC_API_KEY=sk-ant-...
GEMINI_API_KEY=AI...
```

### 2. Install Provider Packages

```bash
# OpenAI (included by default)
pip install openai tiktoken

# Anthropic Claude (optional)
pip install anthropic

# Google Gemini (optional)
pip install google-genai
```

## Usage

### Option 1: Use Default Provider (from settings)

```python
from ai_interactions.services import AIService

# Uses DEFAULT_AI_PROVIDER from settings
ai_service = AIService(user=request.user)
response = ai_service.chat("Hello, how are you?")
```

### Option 2: Specify Provider

```python
# Use OpenAI
ai_service = AIService(user=request.user, provider='openai')

# Use Anthropic
ai_service = AIService(user=request.user, provider='anthropic')

# Use Gemini
ai_service = AIService(user=request.user, provider='gemini')
```

### Option 3: Specify Provider and Model

```python
# GPT-4
ai_service = AIService(user=request.user, provider='openai', model='gpt-4')

# Claude 3 Opus
ai_service = AIService(user=request.user, provider='anthropic', model='claude-3-opus-20240229')

# Gemini 2.5 Flash (recommended - fastest)
ai_service = AIService(user=request.user, provider='gemini', model='gemini-2.5-flash')

# Gemini 2.5 Pro (best quality)
ai_service = AIService(user=request.user, provider='gemini', model='gemini-2.5-pro')
```

### Option 4: Per-Request Provider Selection

Frontend can specify provider in API request:

```bash
curl -X POST http://localhost:8000/api/ai/chat/ \
  -H "Authorization: Bearer TOKEN" \
  -d '{
    "message": "Explain quantum computing",
    "provider": "anthropic"
  }'
```

## API Examples

### Chat with Different Providers

```python
from ai_interactions.services import AIService

# OpenAI GPT-4
openai_service = AIService(user, provider='openai', model='gpt-4')
response = openai_service.chat("Explain quantum computing")

# Anthropic Claude 3
anthropic_service = AIService(user, provider='anthropic', model='claude-3-sonnet-20240229')
response = anthropic_service.chat("Explain quantum computing")

# Google Gemini
gemini_service = AIService(user, provider='gemini')
response = gemini_service.chat("Explain quantum computing")

# All return same AIResponse format:
print(response.content)          # "Quantum computing is..."
print(response.provider)         # "openai", "anthropic", or "gemini"
print(response.model)            # Model used
print(response.total_tokens)     # Token count
print(response.estimated_cost)   # Cost in USD
```

### Streaming Responses

```python
# Stream from any provider
ai_service = AIService(user, provider='openai')

for chunk in ai_service.stream_chat("Tell me a story"):
    print(chunk, end='', flush=True)
```

### Other Features

```python
ai_service = AIService(user)

# Summarize
response = ai_service.summarize(text, length='medium')

# Translate
response = ai_service.translate(text, target_language='Spanish')

# Explain code
response = ai_service.explain_code(code, language='python')

# Count tokens
token_count = ai_service.count_tokens(text)

# Estimate cost
cost = ai_service.estimate_cost(prompt_tokens=100, completion_tokens=200)
```

## Architecture

### Provider Interface (base.py)

All providers implement `BaseAIProvider`:

```python
class BaseAIProvider(ABC):
    @abstractmethod
    def chat(messages, temperature, max_tokens) -> AIResponse
    
    @abstractmethod
    def stream_chat(messages, temperature, max_tokens) -> Generator
    
    @abstractmethod
    def count_tokens(text) -> int
    
    @abstractmethod
    def get_provider_name() -> str
```

### Unified Response Format

All providers return `AIResponse`:

```python
@dataclass
class AIResponse:
    content: str                  # Response text
    model: str                    # Model used
    provider: str                 # Provider name
    prompt_tokens: int            # Tokens in prompt
    completion_tokens: int        # Tokens in response
    total_tokens: int             # Total tokens
    finish_reason: str            # Why generation stopped
    estimated_cost: float         # Cost in USD
```

### Service Layer (services.py)

High-level interface that:
- Handles provider selection
- Builds messages with context
- Integrates user memory
- Manages conversation history

### Factory Pattern (factory.py)

Creates provider instances:

```python
from ai_interactions.providers import get_ai_provider

# Get default provider
provider = get_ai_provider()

# Get specific provider
provider = get_ai_provider('anthropic', model='claude-3-opus-20240229')
```

## Adding a Custom Provider

### 1. Create Provider Class

```python
# ai_interactions/providers/custom_provider.py
from .base import BaseAIProvider, AIMessage, AIResponse

class CustomProvider(BaseAIProvider):
    def get_default_model(self) -> str:
        return 'custom-model-v1'
    
    def get_provider_name(self) -> str:
        return 'custom'
    
    def chat(self, messages, temperature, max_tokens, **kwargs) -> AIResponse:
        # Your implementation
        pass
    
    def stream_chat(self, messages, temperature, max_tokens, **kwargs):
        # Your implementation
        pass
    
    def count_tokens(self, text) -> int:
        # Your implementation
        pass
```

### 2. Register Provider

```python
from ai_interactions.providers.factory import AIProviderFactory
from .custom_provider import CustomProvider

# Register
AIProviderFactory.register_provider('custom', CustomProvider)

# Use
provider = get_ai_provider('custom')
```

### 3. Add Configuration

```python
# settings.py
CUSTOM_API_KEY = os.getenv('CUSTOM_API_KEY', '')

# factory.py - update _get_api_key_from_settings
key_map = {
    'openai': 'OPENAI_API_KEY',
    'anthropic': 'ANTHROPIC_API_KEY',
    'gemini': 'GEMINI_API_KEY',
    'custom': 'CUSTOM_API_KEY',  # Add this
}
```

## Best Practices

### 1. Provider Selection Strategy

```python
# Let users choose in their profile
user.profile.preferred_ai_provider = 'anthropic'

# Use for long-context tasks
if len(context) > 10000:
    provider = 'anthropic'  # Claude handles long context better

# Use for cost optimization
if user.is_premium:
    provider = 'openai'
    model = 'gpt-4'
else:
    provider = 'gemini'  # More cost-effective
```

### 2. Error Handling with Fallback

```python
def chat_with_fallback(user, message):
    providers = ['openai', 'anthropic', 'gemini']
    
    for provider in providers:
        try:
            ai_service = AIService(user, provider=provider)
            return ai_service.chat(message)
        except Exception as e:
            continue  # Try next provider
    
    raise Exception("All providers failed")
```

### 3. Cost Optimization

```python
# Use cheaper models for simple tasks
if task_complexity == 'simple':
    provider = 'openai'
    model = 'gpt-3.5-turbo'
else:
    provider = 'openai'
    model = 'gpt-4'

# Track costs per provider
response = ai_service.chat(message)
log_cost(response.provider, response.estimated_cost)
```

## Token Tracking

All providers normalize token counting:

```python
# Accurate token counting per provider
openai_service = AIService(user, provider='openai')
tokens = openai_service.count_tokens(text)  # Uses tiktoken

anthropic_service = AIService(user, provider='anthropic')
tokens = anthropic_service.count_tokens(text)  # Uses Claude's estimation

# Track in database
TokenUsage.objects.create(
    user=user,
    provider=response.provider,
    model=response.model,
    total_tokens=response.total_tokens,
    estimated_cost=response.estimated_cost
)
```

## Testing

```python
# Test each provider
def test_providers():
    user = User.objects.first()
    message = "Hello, how are you?"
    
    for provider in ['openai', 'anthropic', 'gemini']:
        try:
            ai_service = AIService(user, provider=provider)
            response = ai_service.chat(message)
            print(f"{provider}: {response.content[:50]}...")
        except Exception as e:
            print(f"{provider}: ERROR - {e}")
```

## Troubleshooting

### "Provider not supported"
- Check provider name spelling
- Ensure provider is in `AIProviderFactory.PROVIDERS`

### "API key not found"
- Verify API key in `.env`
- Check setting name matches in `factory.py`

### "Module not found"
- Install provider package: `pip install anthropic` or `pip install google-generativeai`

### "Rate limit exceeded"
- Implement exponential backoff
- Use quota system to limit requests
- Switch to another provider

## Performance Comparison

| Provider | Speed | Context | Quality | Cost |
|----------|-------|---------|---------|------|
| OpenAI GPT-4 | Fast | 128K | Excellent | $$$ |
| Anthropic Claude 3 | Medium | 200K | Excellent | $$ |
| Gemini 2.5 Flash | Very Fast | 1M | Excellent | $ |
| Gemini 2.5 Pro | Fast | 2M | Excellent | $$ |

## Conclusion

The multi-provider architecture gives you:
- **Flexibility**: Switch providers anytime
- **Reliability**: Fallback to alternatives
- **Cost Optimization**: Choose based on budget
- **Future-Proof**: Easy to add new providers

All through a single, unified API! 🚀

