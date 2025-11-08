# AI Assistant API Documentation

## Overview

This is a comprehensive REST API for the AI Desktop Assistant (Jarvis) with real-time WebSocket support. The API provides user authentication, profile management, token usage tracking, AI interactions, and voice command processing.

## Base URL

```
Development: http://localhost:8000
Production: https://your-domain.com
```

## Authentication

The API uses JWT (JSON Web Token) authentication.

### Register
```http
POST /api/auth/register/
Content-Type: application/json

{
  "username": "user123",
  "email": "user@example.com",
  "password": "SecurePass123",
  "password2": "SecurePass123"
}
```

### Login
```http
POST /api/auth/login/
Content-Type: application/json

{
  "username": "user123",
  "password": "SecurePass123"
}

Response:
{
  "refresh": "refresh_token_here",
  "access": "access_token_here"
}
```

### Using the Access Token
Include the access token in the Authorization header for all protected endpoints:

```http
Authorization: Bearer <access_token>
```

## Interactive Documentation

- **Swagger UI**: http://localhost:8000/api/docs/
- **ReDoc**: http://localhost:8000/api/redoc/
- **OpenAPI Schema**: http://localhost:8000/api/schema/

## API Endpoints

### User Profile

- `GET /api/profile/` - Get user profile with settings and token usage
- `PUT /api/profile/` - Update profile (full update)
- `PATCH /api/profile/` - Update profile (partial update)
- `POST /api/profile/reset/` - Reset profile settings to defaults
- `GET /api/profile/usage/` - Get detailed usage statistics

### Token Usage & Quotas

- `GET /api/usage/stats/` - Get aggregated usage statistics
- `GET /api/usage/history/` - Get paginated usage history
- `GET /api/usage/quotas/` - Get current quotas
- `GET /api/usage/cost/` - Get cost breakdown

### AI Interactions

- `GET /api/ai/conversations/` - List user's conversations
- `GET /api/ai/conversations/{id}/` - Get conversation with messages
- `DELETE /api/ai/conversations/{id}/` - Delete conversation
- `GET /api/ai/memory/` - Get user's AI memory

### Voice Commands

- `GET /api/voice/history/` - Get voice command history

## WebSocket Connection

Connect to the WebSocket for real-time communication:

```
ws://localhost:8000/ws/assistant/
```

### WebSocket Message Types

**Client to Server:**

1. AI Request:
```json
{
  "type": "ai_request",
  "data": {
    "message": "Your question here"
  }
}
```

2. Voice Command:
```json
{
  "type": "voice_command",
  "data": {
    "transcribed_text": "Voice command text"
  }
}
```

3. Clipboard Context:
```json
{
  "type": "clipboard_context",
  "data": {
    "content": "Clipboard content"
  }
}
```

**Server to Client:**

1. AI Response:
```json
{
  "type": "ai_response",
  "status": "complete",
  "message": "AI response text",
  "tokens": {
    "prompt": 100,
    "completion": 200,
    "total": 300
  }
}
```

2. Token Usage Update:
```json
{
  "type": "token_usage",
  "daily_used": 5000,
  "daily_limit": 10000,
  "daily_remaining": 5000,
  "monthly_used": 50000,
  "monthly_limit": 100000
}
```

3. Quota Warning:
```json
{
  "type": "quota_warning",
  "level": "daily",
  "percentage_used": 92.5,
  "message": "You have used 92.5% of your daily quota"
}
```

## Response Format

### Success Response
```json
{
  "data": {...},
  "message": "Success message"
}
```

### Error Response
```json
{
  "error": "Error message",
  "details": {...}
}
```

### Pagination
```json
{
  "count": 100,
  "next": "http://localhost:8000/api/endpoint/?page=2",
  "previous": null,
  "results": [...]
}
```

## Token Usage Tracking

All AI requests return token usage information:

```json
{
  "response": "...",
  "tokens": {
    "prompt": 150,
    "completion": 200,
    "total": 350
  },
  "usage_stats": {
    "daily_used": 5420,
    "daily_limit": 10000,
    "daily_remaining": 4580,
    "monthly_used": 45230,
    "monthly_limit": 100000
  }
}
```

## Rate Limiting

- Daily token limits: 10,000 (free) / 50,000 (premium)
- Monthly token limits: 100,000 (free) / 500,000 (premium)
- Quotas reset automatically

## Error Codes

- `400` - Bad Request (invalid data)
- `401` - Unauthorized (authentication required)
- `403` - Forbidden (insufficient permissions)
- `404` - Not Found
- `429` - Too Many Requests (quota exceeded)
- `500` - Internal Server Error

## Development Setup

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Configure environment variables (copy .env.example to .env)

3. Run migrations:
```bash
python manage.py migrate
```

4. Start development server:
```bash
daphne -b 0.0.0.0 -p 8000 config.asgi:application
```

5. Start Celery worker (optional):
```bash
celery -A config worker -l info
```

6. Start Celery beat (optional):
```bash
celery -A config beat -l info
```

## Support

For issues and questions, please refer to the interactive documentation at `/api/docs/`.

