# Jarvis AI Assistant - Quick Reference

## 🚀 Setup

```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Configure environment (.env file)
DEFAULT_AI_PROVIDER=openai
OPENAI_API_KEY=sk-...
ANTHROPIC_API_KEY=sk-ant-...  # Optional
GEMINI_API_KEY=AI...           # Optional

# 3. Run migrations
python manage.py makemigrations
python manage.py migrate

# 4. Start server
python manage.py runserver

# 5. Start Celery (optional, for background tasks)
celery -A config worker -l info
celery -A config beat -l info
```

## 📡 Core Endpoints

| Method | Endpoint | Purpose |
|--------|----------|---------|
| POST | `/api/auth/register/` | Register user |
| POST | `/api/auth/login/` | Login |
| POST | `/api/auth/logout/` | Logout |
| POST | `/api/auth/token/refresh/` | Refresh token |
| GET | `/api/profile/` | Get profile |
| PATCH | `/api/profile/` | Update profile |
| POST | `/api/profile/reset/` | Reset settings |
| **POST** | **`/api/ai/chat/`** | **Main chat endpoint** |
| POST | `/api/ai/summarize/` | Summarize text |
| POST | `/api/ai/translate/` | Translate |
| POST | `/api/ai/explain-code/` | Explain code |
| GET | `/api/ai/conversations/` | List conversations |
| GET | `/api/ai/conversations/{id}/` | Get conversation |
| GET | `/api/token/history/` | Usage history |
| GET | `/api/token/stats/` | Usage stats |
| GET | `/api/token/cost/` | Cost breakdown |

## 🤖 AI Providers

### Supported Providers
- **OpenAI** - GPT-4, GPT-4-Turbo, GPT-3.5-Turbo
- **Anthropic** - Claude 3 (Opus, Sonnet, Haiku)
- **Google Gemini** - Gemini 2.5 Flash, Gemini 2.5 Pro, Gemini 1.5 Pro

### Provider Selection

**Option 1: Default (from .env)**
```bash
DEFAULT_AI_PROVIDER=openai
```

**Option 2: Per Request**
```bash
curl -X POST /api/ai/chat/ -d '{"message": "Hello", "provider": "anthropic"}'
```

**Option 3: Programmatic**
```python
from ai_interactions.services import AIService
ai_service = AIService(user, provider='gemini', model='gemini-pro')
```

## 💬 Chat API

### Basic Chat
```bash
POST /api/ai/chat/
{
  "message": "Your question here"
}
```

### With Provider
```bash
{
  "message": "Your question",
  "provider": "openai"  # or "anthropic", "gemini"
}
```

### With Context
```bash
{
  "message": "Help with this",
  "context": {
    "clipboard": "selected text",
    "active_app": "VS Code"
  }
}
```

### Continue Conversation
```bash
{
  "message": "Follow-up question",
  "conversation_id": 123
}
```

## 📊 Response Format

```json
{
  "message": "AI response text",
  "conversation_id": 123,
  "message_id": 456,
  "tokens": {
    "prompt": 100,
    "completion": 200,
    "total": 300
  },
  "model": "gpt-4-turbo-preview",
  "provider": "openai",
  "usage": {
    "daily_used": 350,
    "daily_limit": 10000,
    "monthly_used": 1500,
    "monthly_limit": 100000
  }
}
```

## 🔑 Authentication

### Register
```bash
POST /api/auth/register/
{"username": "john", "email": "john@ex.com", "password": "pass"}
```

### Login
```bash
POST /api/auth/login/
{"username": "john", "password": "pass"}

# Returns: {"access": "TOKEN", "refresh": "REFRESH_TOKEN"}
```

### Use Token
```bash
curl -H "Authorization: Bearer YOUR_ACCESS_TOKEN" ...
```

### Refresh
```bash
POST /api/auth/token/refresh/
{"refresh": "REFRESH_TOKEN"}
```

## 👤 Profile Management

### Get Profile
```bash
GET /api/profile/
```

### Update Settings
```bash
PATCH /api/profile/
{
  "theme": "dark",
  "ai_response_length": "short",
  "voice_speed": 1.2
}
```

### Check Usage
```bash
GET /api/profile/usage/

# Response:
{
  "daily_remaining": 9850,
  "monthly_remaining": 98500
}
```

## 📈 Token Tracking

### Usage History
```bash
GET /api/token/history/?start_date=2024-01-01
```

### Statistics
```bash
GET /api/token/stats/

# Returns: total_tokens, total_cost, avg_per_request
```

### Cost Breakdown
```bash
GET /api/token/cost/

# Returns: by_feature, by_model, by_date
```

## 🎙️ Voice Features

### Transcribe
```bash
POST /api/voice/transcribe/
-F "audio=@recording.wav"
```

### Text-to-Speech
```bash
POST /api/voice/speak/
{"text": "Hello", "voice": "en-US", "speed": 1.0}
```

## 🌐 WebSocket

```javascript
const ws = new WebSocket('ws://localhost:8000/ws/assistant/');

ws.send(JSON.stringify({
  type: 'chat',
  message: 'Hello',
  provider: 'openai'
}));

ws.onmessage = (event) => {
  const data = JSON.parse(event.data);
  console.log(data);
};
```

## 📚 Documentation

- **Swagger UI**: http://localhost:8000/api/docs/
- **ReDoc**: http://localhost:8000/api/redoc/
- **OpenAPI Schema**: http://localhost:8000/api/schema/

## 🐛 Common Issues

### 1. "API key not found"
**Fix:** Add to `.env`:
```bash
OPENAI_API_KEY=sk-...
```

### 2. "Provider not supported"
**Fix:** Check provider name (must be lowercase):
- `openai` ✅
- `OpenAI` ❌

### 3. "Daily quota exceeded"
**Fix:** Check usage:
```bash
GET /api/profile/usage/
```

### 4. "Database connection failed"
**Fix:** Check PostgreSQL is running:
```bash
sudo systemctl status postgresql
```

### 5. "Module 'anthropic' not found"
**Fix:** Install optional provider:
```bash
pip install anthropic
```

## 🔧 Configuration

### .env Template
```bash
# Django
SECRET_KEY=your-secret-key
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1

# Database
DB_NAME=jarvis
DB_USER=jarvis_user
DB_PASSWORD=your-password
DB_HOST=localhost
DB_PORT=5432

# Redis
REDIS_HOST=localhost
REDIS_PORT=6379

# AI Provider
DEFAULT_AI_PROVIDER=openai
OPENAI_API_KEY=sk-...
ANTHROPIC_API_KEY=sk-ant-...
GEMINI_API_KEY=AI...

# Token Limits
DEFAULT_DAILY_TOKEN_LIMIT=10000
DEFAULT_MONTHLY_TOKEN_LIMIT=100000
```

## 🧪 Testing

```bash
# All tests
python manage.py test

# Specific app
python manage.py test ai_interactions

# With SQLite (faster for testing)
USE_SQLITE=True python manage.py test
```

## 📦 Project Structure

```
ai-assistant/
├── authentication/      # JWT auth
├── profiles/           # User preferences
├── token_usage/        # Usage tracking
├── ai_interactions/    # AI features
│   ├── providers/      # Multi-provider support
│   │   ├── base.py
│   │   ├── openai_provider.py
│   │   ├── anthropic_provider.py
│   │   ├── gemini_provider.py
│   │   └── factory.py
│   ├── services.py     # Service layer
│   └── views.py        # API endpoints
├── voice/              # Voice features
├── realtime/           # Real-time communication (WebSockets)
├── config/             # Django settings
└── docs/               # Documentation
```

## 🎯 Code Examples

### Python Client
```python
import requests

BASE_URL = "http://localhost:8000/api"

# Login
r = requests.post(f"{BASE_URL}/auth/login/", json={
    "username": "john", "password": "pass"
})
token = r.json()['access']

# Chat
headers = {"Authorization": f"Bearer {token}"}
r = requests.post(
    f"{BASE_URL}/ai/chat/",
    headers=headers,
    json={"message": "Hello", "provider": "openai"}
)
print(r.json()['message'])
```

### JavaScript Client
```javascript
const BASE_URL = 'http://localhost:8000/api';

// Login
const response = await fetch(`${BASE_URL}/auth/login/`, {
  method: 'POST',
  headers: {'Content-Type': 'application/json'},
  body: JSON.stringify({username: 'john', password: 'pass'})
});
const {access} = await response.json();

// Chat
const chatResponse = await fetch(`${BASE_URL}/ai/chat/`, {
  method: 'POST',
  headers: {
    'Authorization': `Bearer ${access}`,
    'Content-Type': 'application/json'
  },
  body: JSON.stringify({
    message: 'Hello',
    provider: 'openai'
  })
});
const data = await chatResponse.json();
console.log(data.message);
```

## 🚀 Production Checklist

- [ ] Set `DEBUG=False`
- [ ] Use PostgreSQL (not SQLite)
- [ ] Configure Redis
- [ ] Set strong `SECRET_KEY`
- [ ] Add all API keys to `.env`
- [ ] Set up Celery workers
- [ ] Configure CORS properly
- [ ] Set up HTTPS
- [ ] Enable rate limiting
- [ ] Set up monitoring
- [ ] Configure backups

## 💡 Tips

1. **Provider Selection**: Use cheaper providers (Gemini) for simple tasks, premium (GPT-4) for complex ones
2. **Context**: Always include clipboard/app context for better responses
3. **Conversations**: Continue conversations instead of starting new ones
4. **Quotas**: Monitor usage to avoid hitting limits
5. **Costs**: Check `/api/token/cost/` regularly

## 📞 Need Help?

- Read `/docs/API_DOCUMENTATION.md` for detailed API docs
- Check `/docs/AI_PROVIDERS.md` for provider setup
- See `/docs/USAGE_EXAMPLES.md` for more examples
- Review `/docs/ARCHITECTURE_OVERVIEW.md` for system design

---

**Happy coding! 🎉**

