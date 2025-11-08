# Jarvis AI Assistant - Architecture Overview

## 🏗️ System Architecture

The Jarvis AI Assistant backend is built using Django with a modular, scalable architecture supporting multiple AI providers, real-time communication, and comprehensive usage tracking.

## 📦 Core Components

### 1. **Authentication** (`authentication/`)
- JWT-based authentication (access & refresh tokens)
- User registration and login
- Token refresh and blacklisting
- Secure logout

**API Endpoints:**
- `POST /api/auth/register/` - User registration
- `POST /api/auth/login/` - Login (returns JWT tokens)
- `POST /api/auth/logout/` - Logout (blacklist tokens)
- `POST /api/auth/token/refresh/` - Refresh access token

### 2. **User Profiles** (`profiles/`)
- User preferences and settings
- Theme customization
- AI response length preference
- Notification settings
- Window position preferences
- Voice settings (speed, volume, language)
- Token usage tracking (daily/monthly)
- Premium user management

**API Endpoints:**
- `GET /api/profile/` - Get user profile
- `PUT/PATCH /api/profile/` - Update profile
- `POST /api/profile/reset/` - Reset to defaults
- `GET /api/profile/usage/` - Detailed usage statistics

### 3. **Token Usage Tracking** (`token_usage/`)
- Granular token usage tracking per feature
- Per-model cost tracking
- Daily/monthly usage history
- Quota management (daily, monthly, custom)
- Automatic quota resets
- Cost breakdown by feature and model

**API Endpoints:**
- `GET /api/token/history/` - Token usage history (filterable)
- `GET /api/token/stats/` - Aggregated statistics
- `GET /api/token/quotas/` - User quotas
- `GET /api/token/cost/` - Cost breakdown

### 4. **AI Interactions** (`ai_interactions/`)
- Multi-provider AI integration (OpenAI, Anthropic, Gemini)
- Conversation management
- Message history
- AI memory (user context)
- Context-aware responses
- Specialized features (summarize, translate, explain code)

**AI Provider Architecture:**
```
ai_interactions/
├── providers/
│   ├── base.py              # Abstract base class
│   ├── openai_provider.py   # OpenAI/GPT implementation
│   ├── anthropic_provider.py # Claude implementation
│   ├── gemini_provider.py   # Gemini implementation
│   └── factory.py           # Provider factory
├── services.py              # High-level AI service layer
├── models.py                # Database models
├── views.py                 # API endpoints
└── serializers.py           # Data serialization
```

**API Endpoints:**
- `POST /api/ai/chat/` - Main chat endpoint (supports all providers)
- `POST /api/ai/summarize/` - Summarize text
- `POST /api/ai/translate/` - Translate text
- `POST /api/ai/explain-code/` - Explain code
- `GET /api/ai/conversations/` - List conversations
- `GET /api/ai/conversations/{id}/` - Get conversation
- `DELETE /api/ai/conversations/{id}/` - Delete conversation
- `GET /api/ai/memory/` - Get AI memory

### 5. **Voice Features** (`voice/`)
- Speech-to-text (STT)
- Text-to-speech (TTS)
- Voice command processing
- Voice history

**API Endpoints:**
- `POST /api/voice/transcribe/` - Transcribe audio
- `POST /api/voice/speak/` - Generate speech
- `POST /api/voice/command/` - Process voice command
- `GET /api/voice/history/` - Voice command history

### 6. **WebSocket Communication** (`realtime/`)
- Real-time AI responses
- Bi-directional communication
- Streaming responses
- Live updates

**WebSocket Endpoints:**
- `ws://localhost:8000/ws/assistant/` - Main assistant connection

## 🎯 AI Provider Strategy Pattern

### Design Principle
The system uses the **Strategy Pattern** to support multiple AI providers through a unified interface, making it easy to:
- Switch providers without code changes
- Add new providers easily
- Use different providers per request
- Implement fallback mechanisms
- Compare providers A/B testing

### Provider Interface
All providers implement the `BaseAIProvider` abstract class:

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
All providers return a standardized `AIResponse`:

```python
@dataclass
class AIResponse:
    content: str              # Response text
    model: str                # Model used
    provider: str             # Provider name
    prompt_tokens: int        # Tokens in prompt
    completion_tokens: int    # Tokens in response
    total_tokens: int         # Total tokens
    finish_reason: str        # Why generation stopped
    estimated_cost: float     # Cost in USD
```

### Service Layer
The `AIService` class provides high-level AI operations:

```python
ai_service = AIService(user=request.user, provider='openai')

# Chat
response = ai_service.chat(message, context, conversation_history)

# Streaming
for chunk in ai_service.stream_chat(message):
    print(chunk)

# Specialized tasks
summary = ai_service.summarize(text, length='medium')
translation = ai_service.translate(text, target_language='Spanish')
explanation = ai_service.explain_code(code, language='python')
```

### Provider Selection
Multiple ways to select providers:

1. **Default (from settings)**
   ```python
   DEFAULT_AI_PROVIDER=openai  # .env
   ```

2. **Per request**
   ```bash
   curl -X POST /api/ai/chat/ -d '{"message": "Hello", "provider": "anthropic"}'
   ```

3. **Programmatic**
   ```python
   ai_service = AIService(user, provider='gemini', model='gemini-pro')
   ```

## 🔄 Data Flow

### Chat Request Flow
```
1. Frontend → POST /api/ai/chat/
2. AIChatView validates request
3. Check user quota (daily/monthly limits)
4. AIService builds messages with context
5. Provider (OpenAI/Anthropic/Gemini) processes
6. Save user message to database
7. Get AI response
8. Save AI response to database
9. Update conversation stats
10. Track token usage
11. Update user profile usage
12. Return response to frontend
```

### Token Tracking Flow
```
1. AI response generated
2. Extract token counts from provider
3. Update UserProfile (total, daily, monthly)
4. Create TokenUsage record (detailed)
5. Update UsageQuota if applicable
6. Calculate cost based on model pricing
7. Check if quota exceeded
```

### WebSocket Flow (Real-time)
```
1. Frontend → WebSocket connection
2. Authenticate user
3. Join user's room
4. Stream AI response chunks
5. Send typing indicators
6. Push real-time updates
7. Handle disconnections gracefully
```

## 📊 Database Schema

### Core Models

**User (Django Built-in)**
- username, email, password
- Extended by UserProfile

**UserProfile**
- User preferences (theme, notifications, etc.)
- Voice settings
- Token usage tracking
- Premium status
- Quota limits

**Conversation**
- User
- Title
- Active status
- Total tokens used
- Message count
- Timestamps

**AIMessage**
- Conversation
- Role (user/assistant/system)
- Content
- Context data
- AI model used
- Token counts
- Timestamps

**AIMemory**
- User
- Key facts about user
- Used to personalize responses

**TokenUsage**
- User
- Date
- Feature type (chat/summarize/translate/etc.)
- AI model used
- Token counts
- Estimated cost
- Request count

**UsageQuota**
- User
- Quota type (daily/monthly/custom)
- Limit
- Used
- Reset date
- Active status

**VoiceCommand**
- User
- Audio file path
- Transcribed text
- Command type
- Response
- STT method
- Costs

## 🔐 Security

### Authentication
- JWT tokens (access + refresh)
- Token blacklisting on logout
- Secure password hashing (Django default)
- Token expiration (configurable)

### Authorization
- All endpoints require authentication
- Users can only access their own data
- Profile-based permissions
- Rate limiting via quotas

### API Keys
- AI provider keys stored in environment variables
- Never exposed to frontend
- Loaded via `python-dotenv`

## 🚀 Performance

### Caching (Redis)
```python
CACHES = {
    'default': {
        'BACKEND': 'django_redis.cache.RedisCache',
        'LOCATION': 'redis://localhost:6379/1',
    }
}
```

### Background Tasks (Celery)
- Daily quota resets (scheduled)
- Monthly quota resets (scheduled)
- Asynchronous processing
- Periodic cleanup jobs

### Database Optimization
- Proper indexes on frequently queried fields
- Pagination for list endpoints
- Select/prefetch related queries
- Connection pooling

## 🔧 Configuration

### Environment Variables
```bash
# Django
SECRET_KEY=...
DEBUG=False
ALLOWED_HOSTS=localhost,127.0.0.1

# Database
DB_NAME=jarvis
DB_USER=jarvis_user
DB_PASSWORD=...
DB_HOST=localhost
DB_PORT=5432

# Redis
REDIS_HOST=localhost
REDIS_PORT=6379

# AI Providers
DEFAULT_AI_PROVIDER=openai
OPENAI_API_KEY=sk-...
ANTHROPIC_API_KEY=sk-ant-...
GEMINI_API_KEY=AI...

# Token Limits
DEFAULT_DAILY_TOKEN_LIMIT=10000
DEFAULT_MONTHLY_TOKEN_LIMIT=100000
PREMIUM_DAILY_TOKEN_LIMIT=50000
PREMIUM_MONTHLY_TOKEN_LIMIT=500000
```

## 📈 Scalability

### Horizontal Scaling
- Stateless API design
- Load balancer ready
- Shared Redis for WebSockets
- Celery distributed task queue

### Vertical Scaling
- Efficient database queries
- Connection pooling
- Caching layer
- Async operations

## 🛠️ Tech Stack

- **Framework:** Django 5.0+
- **API:** Django REST Framework
- **Database:** PostgreSQL (with SQLite fallback for dev)
- **Cache/Queue:** Redis
- **WebSockets:** Django Channels + Daphne
- **Background Tasks:** Celery
- **AI Providers:** OpenAI, Anthropic, Gemini
- **Documentation:** drf-spectacular (OpenAPI/Swagger)
- **Authentication:** JWT (djangorestframework-simplejwt)

## 📚 API Documentation

### Interactive Docs
- **Swagger UI:** http://localhost:8000/api/docs/
- **ReDoc:** http://localhost:8000/api/redoc/
- **OpenAPI Schema:** http://localhost:8000/api/schema/

### Auto-generated
All endpoints are documented using `drf-spectacular`:
- Request/response schemas
- Authentication requirements
- Parameter descriptions
- Example requests/responses

## 🧪 Testing

### Test Structure
```
app/
├── tests.py          # Comprehensive tests
├── models.py         # Test models first (TDD)
└── views.py          # Implement until tests pass
```

### Test Coverage
- Model tests (creation, validation, methods)
- API tests (endpoints, permissions, responses)
- Signal tests (auto-creation, updates)
- Integration tests (end-to-end flows)

### Running Tests
```bash
# All tests
python manage.py test

# Specific app
python manage.py test profiles

# With coverage
coverage run --source='.' manage.py test
coverage report
```

## 🔄 Development Workflow

1. **TDD Approach**
   - Write tests first
   - Implement feature
   - Run tests
   - Refactor if needed

2. **Provider Addition**
   - Create provider class (inherit BaseAIProvider)
   - Implement required methods
   - Register in factory
   - Add API key to settings
   - Test integration

3. **Feature Addition**
   - Create model (if needed)
   - Write tests
   - Create serializer
   - Create view
   - Add URL route
   - Update API docs

## 🎯 Design Decisions

### Why Django?
- Robust ORM for complex queries
- Built-in admin interface
- Strong security features
- Large ecosystem
- Excellent documentation

### Why PostgreSQL?
- Advanced features (JSON, full-text search)
- ACID compliance
- Scalability
- Wide adoption
- Strong community

### Why Multi-Provider Support?
- Avoid vendor lock-in
- Cost optimization
- Feature comparison
- Reliability (fallback)
- Future-proof

### Why JWT?
- Stateless (scalable)
- Cross-domain support
- Mobile-friendly
- Standard (RFC 7519)

### Why Redis?
- Fast caching
- WebSocket channel layer
- Celery broker
- Session storage
- Multi-purpose

## 🔜 Future Enhancements

1. **Provider Auto-Failover**
   - Automatic retry with different provider
   - Cost-based provider selection
   - Load balancing between providers

2. **Advanced Analytics**
   - User behavior tracking
   - A/B testing framework
   - Cost optimization suggestions
   - Usage patterns analysis

3. **Enhanced AI Memory**
   - Long-term memory storage
   - Semantic search in history
   - Context summarization
   - Personalized learning

4. **Multi-Tenancy**
   - Organization support
   - Team collaboration
   - Shared conversations
   - Role-based access

5. **Plugin System**
   - Custom providers
   - Feature extensions
   - Webhook integrations
   - Third-party plugins

## 📞 Support

For detailed documentation:
- `/docs/API_DOCUMENTATION.md` - API reference
- `/docs/AI_PROVIDERS.md` - Provider setup
- `/docs/DATABASE_SETUP.md` - Database configuration
- `/docs/IMPLEMENTATION_SUMMARY.md` - Implementation details

## 🎉 Conclusion

The Jarvis AI Assistant backend provides a **robust, scalable, and extensible** foundation for building AI-powered desktop applications. The multi-provider architecture ensures flexibility, while comprehensive tracking and quota systems enable fine-grained control over usage and costs.

**Key Strengths:**
- ✅ Multi-provider AI support (OpenAI, Anthropic, Gemini)
- ✅ Real-time communication via WebSockets
- ✅ Comprehensive token tracking and cost management
- ✅ User customization and preferences
- ✅ Secure JWT authentication
- ✅ Production-ready architecture
- ✅ Extensive API documentation
- ✅ Test-driven development
- ✅ Scalable design

Ready for deployment! 🚀

