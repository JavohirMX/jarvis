# Jarvis AI Assistant - Usage Examples

## 🚀 Quick Start Examples

### 1. Basic Chat (Default Provider)

```bash
# Register user
curl -X POST http://localhost:8000/api/auth/register/ \
  -H "Content-Type: application/json" \
  -d '{
    "username": "john",
    "email": "john@example.com",
    "password": "SecurePass123"
  }'

# Login
curl -X POST http://localhost:8000/api/auth/login/ \
  -H "Content-Type: application/json" \
  -d '{
    "email": "john@example.com",
    "password": "SecurePass123"
  }'

# Response:
{
  "access": "eyJ0eXAiOiJKV1QiLCJhbGc...",
  "refresh": "eyJ0eXAiOiJKV1QiLCJhbGc..."
}

# Chat with AI (uses DEFAULT_AI_PROVIDER from .env)
curl -X POST http://localhost:8000/api/ai/chat/ \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "message": "Explain quantum computing in simple terms"
  }'
```

### 2. Chat with Specific Provider

```bash
# Use OpenAI GPT-4
curl -X POST http://localhost:8000/api/ai/chat/ \
  -H "Authorization: Bearer TOKEN" \
  -d '{
    "message": "Write a Python function to sort a list",
    "provider": "openai"
  }'

# Use Anthropic Claude
curl -X POST http://localhost:8000/api/ai/chat/ \
  -H "Authorization: Bearer TOKEN" \
  -d '{
    "message": "Analyze this essay and provide feedback",
    "provider": "anthropic"
  }'

# Use Google Gemini
curl -X POST http://localhost:8000/api/ai/chat/ \
  -H "Authorization: Bearer TOKEN" \
  -d '{
    "message": "Summarize the latest news",
    "provider": "gemini"
  }'
```

### 3. Chat with Context

```bash
# Include clipboard and active app context
curl -X POST http://localhost:8000/api/ai/chat/ \
  -H "Authorization: Bearer TOKEN" \
  -d '{
    "message": "Help me with this",
    "context": {
      "clipboard": "def hello():\n    print(\"Hello World\")",
      "active_app": "VS Code"
    }
  }'
```

### 4. Continuing a Conversation

```bash
# First message (creates conversation)
curl -X POST http://localhost:8000/api/ai/chat/ \
  -H "Authorization: Bearer TOKEN" \
  -d '{
    "message": "What is machine learning?"
  }'

# Response includes conversation_id:
{
  "message": "Machine learning is...",
  "conversation_id": 123,
  ...
}

# Continue conversation (AI remembers context)
curl -X POST http://localhost:8000/api/ai/chat/ \
  -H "Authorization: Bearer TOKEN" \
  -d '{
    "message": "Can you explain neural networks?",
    "conversation_id": 123
  }'
```

## 📝 Specialized Features

### Summarize Text

```bash
# Short summary
curl -X POST http://localhost:8000/api/ai/summarize/ \
  -H "Authorization: Bearer TOKEN" \
  -d '{
    "text": "Long article text here...",
    "length": "short"
  }'

# Medium summary (default)
curl -X POST http://localhost:8000/api/ai/summarize/ \
  -H "Authorization: Bearer TOKEN" \
  -d '{
    "text": "Long article text here...",
    "length": "medium"
  }'

# Long detailed summary
curl -X POST http://localhost:8000/api/ai/summarize/ \
  -H "Authorization: Bearer TOKEN" \
  -d '{
    "text": "Long article text here...",
    "length": "long"
  }'
```

### Translate Text

```bash
# Translate to Spanish
curl -X POST http://localhost:8000/api/ai/translate/ \
  -H "Authorization: Bearer TOKEN" \
  -d '{
    "text": "Hello, how are you?",
    "target_language": "Spanish"
  }'

# Response:
{
  "translation": "Hola, ¿cómo estás?",
  "tokens": {"total": 25},
  "model": "gpt-4-turbo-preview",
  "provider": "openai"
}

# Translate to French
curl -X POST http://localhost:8000/api/ai/translate/ \
  -H "Authorization: Bearer TOKEN" \
  -d '{
    "text": "Good morning",
    "target_language": "French"
  }'
```

### Explain Code

```bash
# Explain Python code
curl -X POST http://localhost:8000/api/ai/explain-code/ \
  -H "Authorization: Bearer TOKEN" \
  -d '{
    "code": "def fibonacci(n):\n    if n <= 1:\n        return n\n    return fibonacci(n-1) + fibonacci(n-2)",
    "language": "python"
  }'

# Auto-detect language
curl -X POST http://localhost:8000/api/ai/explain-code/ \
  -H "Authorization: Bearer TOKEN" \
  -d '{
    "code": "function hello() { console.log(\"Hi\"); }"
  }'
```

## 👤 User Profile Management

### Get Profile

```bash
curl -X GET http://localhost:8000/api/profile/ \
  -H "Authorization: Bearer TOKEN"

# Response:
{
  "id": 1,
  "user": {
    "id": 1,
    "username": "john",
    "email": "john@example.com"
  },
  "theme": "dark",
  "ai_response_length": "medium",
  "enable_notifications": true,
  "window_position_x": 100,
  "window_position_y": 50,
  "window_width": 400,
  "window_height": 600,
  "voice_enabled": true,
  "voice_speed": 1.0,
  "voice_volume": 0.8,
  "voice_language": "en-US",
  "is_premium_user": false,
  "daily_remaining": 9850,
  "monthly_remaining": 98500,
  "created_at": "2024-01-15T10:30:00Z",
  "updated_at": "2024-01-15T14:20:00Z"
}
```

### Update Profile

```bash
# Update theme and preferences
curl -X PATCH http://localhost:8000/api/profile/ \
  -H "Authorization: Bearer TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "theme": "light",
    "ai_response_length": "short",
    "enable_notifications": false,
    "voice_speed": 1.2
  }'

# Update window position
curl -X PATCH http://localhost:8000/api/profile/ \
  -H "Authorization: Bearer TOKEN" \
  -d '{
    "window_position_x": 200,
    "window_position_y": 100,
    "window_width": 500,
    "window_height": 700
  }'
```

### Reset Profile to Defaults

```bash
curl -X POST http://localhost:8000/api/profile/reset/ \
  -H "Authorization: Bearer TOKEN"
```

### Get Usage Statistics

```bash
curl -X GET http://localhost:8000/api/profile/usage/ \
  -H "Authorization: Bearer TOKEN"

# Response:
{
  "total_tokens": 1500,
  "daily_tokens": 150,
  "monthly_tokens": 1500,
  "daily_limit": 10000,
  "monthly_limit": 100000,
  "daily_remaining": 9850,
  "monthly_remaining": 98500,
  "is_premium": false
}
```

## 📊 Token Usage Tracking

### View Usage History

```bash
# Get all usage history
curl -X GET http://localhost:8000/api/token/history/ \
  -H "Authorization: Bearer TOKEN"

# Filter by date range
curl -X GET "http://localhost:8000/api/token/history/?start_date=2024-01-01&end_date=2024-01-31" \
  -H "Authorization: Bearer TOKEN"

# Filter by feature type
curl -X GET "http://localhost:8000/api/token/history/?feature_type=chat" \
  -H "Authorization: Bearer TOKEN"

# Filter by AI model
curl -X GET "http://localhost:8000/api/token/history/?model=gpt-4" \
  -H "Authorization: Bearer TOKEN"
```

### Get Usage Statistics

```bash
curl -X GET http://localhost:8000/api/token/stats/ \
  -H "Authorization: Bearer TOKEN"

# Response:
{
  "total_tokens": 15000,
  "total_cost": 0.45,
  "total_requests": 50,
  "average_tokens_per_request": 300,
  "date_range": {
    "start": "2024-01-01",
    "end": "2024-01-31"
  }
}
```

### Get Quota Information

```bash
curl -X GET http://localhost:8000/api/token/quotas/ \
  -H "Authorization: Bearer TOKEN"

# Response:
{
  "quotas": [
    {
      "id": 1,
      "type": "daily",
      "limit": 10000,
      "used": 150,
      "remaining": 9850,
      "reset_date": "2024-01-16T00:00:00Z",
      "is_active": true
    },
    {
      "id": 2,
      "type": "monthly",
      "limit": 100000,
      "used": 1500,
      "remaining": 98500,
      "reset_date": "2024-02-01T00:00:00Z",
      "is_active": true
    }
  ]
}
```

### Get Cost Breakdown

```bash
curl -X GET http://localhost:8000/api/token/cost/ \
  -H "Authorization: Bearer TOKEN"

# Response:
{
  "total_cost": 1.25,
  "by_feature": {
    "chat": 0.80,
    "summarize": 0.25,
    "translate": 0.15,
    "explain_code": 0.05
  },
  "by_model": {
    "gpt-4": 0.90,
    "gpt-3.5-turbo": 0.35
  },
  "by_date": [
    {
      "date": "2024-01-15",
      "cost": 0.45
    },
    {
      "date": "2024-01-16",
      "cost": 0.80
    }
  ]
}
```

## 💬 Conversation Management

### List Conversations

```bash
# Get all conversations
curl -X GET http://localhost:8000/api/ai/conversations/ \
  -H "Authorization: Bearer TOKEN"

# Paginated
curl -X GET "http://localhost:8000/api/ai/conversations/?page=1&page_size=10" \
  -H "Authorization: Bearer TOKEN"
```

### Get Conversation Details

```bash
curl -X GET http://localhost:8000/api/ai/conversations/123/ \
  -H "Authorization: Bearer TOKEN"

# Response includes all messages:
{
  "id": 123,
  "title": "Discussion about machine learning",
  "is_active": true,
  "total_tokens_used": 1500,
  "message_count": 6,
  "created_at": "2024-01-15T10:00:00Z",
  "updated_at": "2024-01-15T11:30:00Z",
  "messages": [
    {
      "id": 1,
      "role": "user",
      "content": "What is machine learning?",
      "created_at": "2024-01-15T10:00:00Z"
    },
    {
      "id": 2,
      "role": "assistant",
      "content": "Machine learning is...",
      "created_at": "2024-01-15T10:00:05Z"
    }
  ]
}
```

### Delete Conversation

```bash
curl -X DELETE http://localhost:8000/api/ai/conversations/123/ \
  -H "Authorization: Bearer TOKEN"
```

### Get AI Memory

```bash
curl -X GET http://localhost:8000/api/ai/memory/ \
  -H "Authorization: Bearer TOKEN"

# Response:
{
  "id": 1,
  "key_facts": "User is a Python developer interested in machine learning. Prefers detailed explanations.",
  "created_at": "2024-01-15T10:00:00Z",
  "updated_at": "2024-01-15T14:30:00Z"
}
```

## 🎙️ Voice Features

### Transcribe Audio

```bash
curl -X POST http://localhost:8000/api/voice/transcribe/ \
  -H "Authorization: Bearer TOKEN" \
  -F "audio=@recording.wav"

# Response:
{
  "transcription": "Hello, can you help me with Python?",
  "duration": 3.5,
  "tokens": 12
}
```

### Text-to-Speech

```bash
curl -X POST http://localhost:8000/api/voice/speak/ \
  -H "Authorization: Bearer TOKEN" \
  -d '{
    "text": "Hello, how can I help you today?",
    "voice": "en-US-Neural",
    "speed": 1.0
  }'

# Response:
{
  "audio_url": "/media/voice/response_123.mp3",
  "duration": 2.8,
  "characters": 35
}
```

### Process Voice Command

```bash
curl -X POST http://localhost:8000/api/voice/command/ \
  -H "Authorization: Bearer TOKEN" \
  -F "audio=@command.wav"

# Response:
{
  "transcription": "Summarize the clipboard content",
  "command_type": "summarize",
  "response": "Here's a summary...",
  "audio_response_url": "/media/voice/response_124.mp3"
}
```

### Voice History

```bash
curl -X GET http://localhost:8000/api/voice/history/ \
  -H "Authorization: Bearer TOKEN"
```

## 🔐 Authentication

### Register

```bash
curl -X POST http://localhost:8000/api/auth/register/ \
  -H "Content-Type: application/json" \
  -d '{
    "username": "alice",
    "email": "alice@example.com",
    "password": "SecurePass123"
  }'
```

### Login

```bash
curl -X POST http://localhost:8000/api/auth/login/ \
  -H "Content-Type: application/json" \
  -d '{
    "username": "alice",
    "password": "SecurePass123"
  }'

# Response:
{
  "access": "eyJ0eXAiOiJKV1QiLCJhbGc...",
  "refresh": "eyJ0eXAiOiJKV1QiLCJhbGc...",
  "user": {
    "id": 2,
    "username": "alice",
    "email": "alice@example.com"
  }
}
```

### Refresh Token

```bash
curl -X POST http://localhost:8000/api/auth/token/refresh/ \
  -H "Content-Type: application/json" \
  -d '{
    "refresh": "eyJ0eXAiOiJKV1QiLCJhbGc..."
  }'

# Response:
{
  "access": "eyJ0eXAiOiJKV1QiLCJhbGc..."
}
```

### Logout

```bash
curl -X POST http://localhost:8000/api/auth/logout/ \
  -H "Authorization: Bearer TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "refresh_token": "eyJ0eXAiOiJKV1QiLCJhbGc..."
  }'
```

## 🌐 WebSocket Examples

### JavaScript Client

```javascript
// Connect to WebSocket
const ws = new WebSocket('ws://localhost:8000/ws/assistant/');

// Connection opened
ws.addEventListener('open', (event) => {
  console.log('Connected to AI Assistant');
  
  // Send message
  ws.send(JSON.stringify({
    type: 'chat',
    message: 'Hello, AI!',
    provider: 'openai'
  }));
});

// Listen for messages
ws.addEventListener('message', (event) => {
  const data = JSON.parse(event.data);
  console.log('Response:', data);
  
  if (data.type === 'streaming_chunk') {
    // Append chunk to response
    console.log(data.content);
  } else if (data.type === 'complete') {
    console.log('Response complete');
  }
});

// Handle errors
ws.addEventListener('error', (error) => {
  console.error('WebSocket error:', error);
});

// Connection closed
ws.addEventListener('close', (event) => {
  console.log('Disconnected from AI Assistant');
});
```

### Python Client

```python
import websocket
import json

def on_message(ws, message):
    data = json.loads(message)
    print(f"Received: {data}")

def on_error(ws, error):
    print(f"Error: {error}")

def on_close(ws, close_status_code, close_msg):
    print("Connection closed")

def on_open(ws):
    print("Connected")
    # Send message
    ws.send(json.dumps({
        "type": "chat",
        "message": "Hello from Python!",
        "provider": "anthropic"
    }))

# Connect
ws = websocket.WebSocketApp(
    "ws://localhost:8000/ws/assistant/",
    on_open=on_open,
    on_message=on_message,
    on_error=on_error,
    on_close=on_close
)

ws.run_forever()
```

## 🧪 Testing Examples

### Python Requests

```python
import requests

# Base URL
BASE_URL = "http://localhost:8000/api"

# Register
response = requests.post(f"{BASE_URL}/auth/register/", json={
    "username": "testuser",
    "email": "test@example.com",
    "password": "TestPass123"
})
print(response.json())

# Login
response = requests.post(f"{BASE_URL}/auth/login/", json={
    "username": "testuser",
    "password": "TestPass123"
})
tokens = response.json()
access_token = tokens['access']

# Chat with AI
headers = {"Authorization": f"Bearer {access_token}"}
response = requests.post(
    f"{BASE_URL}/ai/chat/",
    headers=headers,
    json={
        "message": "Explain recursion",
        "provider": "openai"
    }
)
print(response.json())

# Get profile
response = requests.get(f"{BASE_URL}/profile/", headers=headers)
print(response.json())
```

## 💡 Advanced Usage

### Provider Comparison

```python
import requests

def compare_providers(message):
    """Compare responses from different providers"""
    providers = ['openai', 'anthropic', 'gemini']
    results = {}
    
    for provider in providers:
        response = requests.post(
            f"{BASE_URL}/ai/chat/",
            headers=headers,
            json={"message": message, "provider": provider}
        )
        data = response.json()
        results[provider] = {
            'content': data['message'][:100],  # First 100 chars
            'tokens': data['tokens']['total'],
            'model': data.get('model', 'unknown')
        }
    
    return results

# Compare
results = compare_providers("Explain quantum computing")
for provider, data in results.items():
    print(f"\n{provider}:")
    print(f"  Response: {data['content']}...")
    print(f"  Tokens: {data['tokens']}")
    print(f"  Model: {data['model']}")
```

### Cost Tracking

```python
def track_daily_cost():
    """Get today's AI usage cost"""
    response = requests.get(
        f"{BASE_URL}/token/cost/",
        headers=headers
    )
    data = response.json()
    
    print(f"Total cost today: ${data['total_cost']:.2f}")
    print("\nBy feature:")
    for feature, cost in data['by_feature'].items():
        print(f"  {feature}: ${cost:.2f}")
    
    print("\nBy model:")
    for model, cost in data['by_model'].items():
        print(f"  {model}: ${cost:.2f}")

track_daily_cost()
```

### Batch Processing

```python
def batch_summarize(texts):
    """Summarize multiple texts"""
    summaries = []
    
    for text in texts:
        response = requests.post(
            f"{BASE_URL}/ai/summarize/",
            headers=headers,
            json={"text": text, "length": "short"}
        )
        summaries.append(response.json()['summary'])
    
    return summaries

texts = [
    "Long article 1...",
    "Long article 2...",
    "Long article 3..."
]

summaries = batch_summarize(texts)
for i, summary in enumerate(summaries, 1):
    print(f"Summary {i}: {summary}")
```

## 🎯 Best Practices

1. **Always include Authorization header**
   ```bash
   -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
   ```

2. **Handle token expiration**
   - Refresh token when you get 401 Unauthorized
   - Store refresh token securely

3. **Check quotas before expensive operations**
   ```bash
   # Check remaining quota
   curl -X GET http://localhost:8000/api/profile/usage/ -H "Authorization: Bearer TOKEN"
   ```

4. **Use appropriate provider for task**
   - OpenAI: General chat, code
   - Anthropic: Long context, analysis
   - Gemini: Fast responses, cost-effective

5. **Include context when relevant**
   - Clipboard content
   - Active application
   - Previous messages

6. **Monitor costs**
   - Check `/api/token/cost/` regularly
   - Set up alerts for high usage

## 🚀 Ready to Build!

You now have all the examples you need to integrate with the Jarvis AI Assistant backend. Happy coding! 🎉

