# AI Desktop Assistant (Jarvis) - Backend API

A comprehensive Django REST API backend for an AI-powered desktop assistant that monitors clipboard, provides context-aware help, and supports voice commands.

## Features

### ✅ Implemented

- **User Authentication** - JWT-based authentication with registration, login, logout
- **User Profiles** - Customizable settings (theme, AI response length, notifications, voice preferences)
- **Avatar Upload** - Profile picture support with MinIO/S3-compatible object storage
- **Token Usage Tracking** - Comprehensive tracking and quota management for AI API usage
- **AI Interactions** - Conversation management, message history, and AI memory
- **Voice Commands** - Support for voice transcription and text-to-speech
- **Real-time WebSocket** - Live communication for AI responses and token updates
- **API Documentation** - Interactive Swagger UI and ReDoc documentation
- **Admin Interface** - Full Django admin for all models
- **PostgreSQL Support** - Production-ready database configuration

## Technology Stack

- **Framework**: Django 5.2+ with Django REST Framework
- **Database**: PostgreSQL (with SQLite fallback for development)
- **Object Storage**: MinIO (S3-compatible, for avatar uploads)
- **WebSocket**: Django Channels with Redis
- **Task Queue**: Celery with Redis broker
- **API Docs**: drf-spectacular (OpenAPI 3.0)
- **Authentication**: JWT (djangorestframework-simplejwt)
- **AI Integration**: OpenAI, Anthropic Claude, Google Gemini

## Project Structure

```
ai-assistant/
├── authentication/         # User authentication (JWT)
├── profiles/              # User profiles and settings
├── token_usage/           # Token tracking and quotas
├── ai_interactions/       # AI conversations and memory
├── voice/                 # Voice commands
├── realtime/              # WebSocket consumers (real-time communication)
├── config/                # Project settings
├── docs/                  # Documentation
│   ├── DATABASE_SETUP.md
│   ├── MINIO_SETUP.md
│   └── API_DOCUMENTATION.md
├── requirements.txt
├── .env.example
└── manage.py
```

## Quick Start

### 1. Prerequisites

- Python 3.10+
- PostgreSQL 14+ (optional, can use SQLite for development)
- Redis 6+ (for WebSocket and Celery)
- MinIO (optional, for avatar/media storage - can use local storage)

### 2. Installation

```bash
# Clone the repository
git clone <repository-url>
cd ai-assistant

# Create virtual environment
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Copy environment variables
cp .env.example .env
# Edit .env with your settings
```

### 3. Database Setup

**Option A: SQLite (Development)**
```bash
export USE_SQLITE=True
python manage.py migrate
python manage.py createsuperuser
```

**Option B: PostgreSQL (Production)**
```bash
# See docs/DATABASE_SETUP.md for detailed PostgreSQL setup
python manage.py migrate
python manage.py createsuperuser
```

### 4. MinIO Setup (Optional - for Avatar/Media Storage)

**Option A: Local File Storage (Default)**
```bash
# No additional setup required
# Files stored in media/ directory
USE_MINIO=False
```

**Option B: MinIO Object Storage**
```bash
# Start MinIO with Docker
docker run -d \
  -p 9000:9000 \
  -p 9001:9001 \
  --name minio \
  -e "MINIO_ROOT_USER=minioadmin" \
  -e "MINIO_ROOT_PASSWORD=minioadmin" \
  minio/minio server /data --console-address ":9001"

# Configure in .env
USE_MINIO=True
MINIO_ENDPOINT=http://localhost:9000
MINIO_ACCESS_KEY=minioadmin
MINIO_SECRET_KEY=minioadmin
MINIO_BUCKET_NAME=jarvis-media

# Test MinIO connectivity
python manage.py test_minio
```

**Access MinIO Console**: http://localhost:9001

See [docs/MINIO_SETUP.md](docs/MINIO_SETUP.md) for detailed configuration and production setup.

### 5. Run the Application

**Development Server (with WebSocket support):**
```bash
daphne -b 0.0.0.0 -p 8000 config.asgi:application
```

**Celery Worker (optional, for background tasks):**
```bash
# In a separate terminal
celery -A config worker -l info
```

**Celery Beat (optional, for scheduled tasks):**
```bash
# In another terminal
celery -A config beat -l info
```

### 6. Access the Application

- **Admin Panel**: http://localhost:8000/admin/
- **API Documentation (Swagger)**: http://localhost:8000/api/docs/
- **API Documentation (ReDoc)**: http://localhost:8000/api/redoc/
- **WebSocket**: ws://localhost:8000/ws/assistant/
- **MinIO Console**: http://localhost:9001 (if using MinIO)

## API Endpoints

### Authentication
- `POST /api/auth/register/` - Register new user
- `POST /api/auth/login/` - Login and get JWT tokens
- `POST /api/auth/logout/` - Logout (blacklist refresh token)
- `GET /api/auth/user/` - Get current user details

### User Profile
- `GET /api/profile/` - Get user profile with avatar URL
- `PUT/PATCH /api/profile/` - Update profile settings
- `PATCH /api/profile/` - Upload avatar (multipart/form-data)
- `POST /api/profile/reset/` - Reset to defaults
- `GET /api/profile/usage/` - Get usage statistics

### Token Usage
- `GET /api/usage/stats/` - Usage statistics
- `GET /api/usage/history/` - Usage history
- `GET /api/usage/quotas/` - Current quotas
- `GET /api/usage/cost/` - Cost breakdown

### AI Interactions
- `GET /api/ai/conversations/` - List conversations
- `GET /api/ai/conversations/{id}/` - Get conversation
- `DELETE /api/ai/conversations/{id}/` - Delete conversation
- `GET /api/ai/memory/` - Get AI memory

### Voice Commands
- `GET /api/voice/history/` - Voice command history

## Testing

Run all tests with TDD approach:

```bash
# Test all apps
USE_SQLITE=True python manage.py test --verbosity=2

# Test specific app
USE_SQLITE=True python manage.py test profiles --verbosity=2
```

**Test Coverage:**
- ✅ profiles: 16 tests
- ✅ token_usage: 19 tests
- ✅ ai_interactions: 11 tests
- ✅ voice: 2 tests

**Total: 48 tests passing**

## Configuration

### Environment Variables

Key environment variables (see `.env.example`):

```env
# Django
SECRET_KEY=your-secret-key
DEBUG=True

# Database
DB_NAME=jarvis
DB_USER=ai_assistant_user
DB_PASSWORD=your-password

# Redis
REDIS_HOST=localhost
REDIS_PORT=6379

# AI API Keys
OPENAI_API_KEY=your-key-here

# Token Limits
DEFAULT_DAILY_TOKEN_LIMIT=10000
DEFAULT_MONTHLY_TOKEN_LIMIT=100000
```

### Token Limits

**Free Users:**
- Daily: 10,000 tokens
- Monthly: 100,000 tokens

**Premium Users:**
- Daily: 50,000 tokens
- Monthly: 500,000 tokens

## WebSocket Protocol

### Connection
```javascript
const ws = new WebSocket('ws://localhost:8000/ws/assistant/');
```

### Message Types

**Client → Server:**
```json
{
  "type": "ai_request",
  "data": { "message": "Your question" }
}
```

**Server → Client:**
```json
{
  "type": "ai_response",
  "status": "complete",
  "message": "AI response",
  "tokens": { "total": 300 }
}
```

See `docs/API_DOCUMENTATION.md` for complete WebSocket documentation.

## Development

### Code Quality
- Follow PEP 8 style guide
- Write tests first (TDD approach)
- Document all API endpoints with drf-spectacular decorators
- Use type hints where applicable

### Adding a New Feature
1. Write tests first in `app/tests.py`
2. Run tests to see them fail
3. Implement the feature
4. Run tests to see them pass
5. Add API documentation

## Deployment

### Production Checklist
- [ ] Set `DEBUG=False`
- [ ] Configure proper `SECRET_KEY`
- [ ] Set up PostgreSQL database
- [ ] Configure Redis for production
- [ ] Set up proper CORS origins
- [ ] Configure static files serving
- [ ] Set up SSL/TLS
- [ ] Configure logging
- [ ] Set up monitoring
- [ ] Configure backup strategy

### Recommended Stack
- **Web Server**: Nginx
- **ASGI Server**: Daphne or Uvicorn
- **Database**: PostgreSQL
- **Cache/Queue**: Redis
- **Task Queue**: Celery
- **Monitoring**: Sentry

## Troubleshooting

### Database Connection Issues
- Check PostgreSQL is running: `sudo systemctl status postgresql`
- Verify credentials in `.env`
- Use SQLite for development: `export USE_SQLITE=True`

### WebSocket Connection Issues
- Check Redis is running: `redis-cli ping`
- Verify channel layers configuration
- Check CORS settings for WebSocket

### Token Limit Issues
- Check user's current usage: `GET /api/profile/usage/`
- Reset quotas in admin panel
- Upgrade to premium for higher limits

## Contributing

1. Fork the repository
2. Create a feature branch
3. Write tests for new features
4. Implement the feature
5. Ensure all tests pass
6. Submit a pull request

## License

[Your License Here]

## Support

For issues and questions:
- Check the API documentation: http://localhost:8000/api/docs/
- Review `docs/API_DOCUMENTATION.md`
- Contact support: [your-email@example.com]

## Roadmap

### Planned Features
- [ ] OpenAI GPT-4 integration
- [ ] Anthropic Claude integration
- [ ] Whisper API for STT
- [ ] ElevenLabs TTS integration
- [ ] Rate limiting middleware
- [ ] Usage analytics dashboard
- [ ] Multi-language support
- [ ] Export conversation history
- [ ] Advanced AI memory system

## Acknowledgments

Built with Django, DRF, Channels, and modern Python best practices.

