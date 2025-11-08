# Database Setup Guide

## PostgreSQL Setup for AI Assistant (Jarvis)

### 1. Install PostgreSQL
```bash
# Ubuntu/Debian
sudo apt update
sudo apt install postgresql postgresql-contrib

# Start PostgreSQL service
sudo systemctl start postgresql
sudo systemctl enable postgresql
```

### 2. Create Database and User
```bash
# Switch to postgres user
sudo -u postgres psql

# In PostgreSQL shell, run:
CREATE DATABASE jarvis;
CREATE USER jarvis_user WITH PASSWORD 'your_secure_password';
ALTER ROLE jarvis_user SET client_encoding TO 'utf8';
ALTER ROLE jarvis_user SET default_transaction_isolation TO 'read committed';
ALTER ROLE jarvis_user SET timezone TO 'UTC';
GRANT ALL PRIVILEGES ON DATABASE jarvis TO jarvis_user;

# For PostgreSQL 15+, also grant schema privileges:
\c jarvis
GRANT ALL ON SCHEMA public TO jarvis_user;

# Exit PostgreSQL shell
\q
```

### 3. Update Environment Variables
Copy `.env.example` to `.env` and update database credentials:
```bash
cp .env.example .env
# Edit .env with your actual database password
```

### 4. Run Migrations
```bash
# Activate virtual environment
source .venv/bin/activate

# Run migrations
python manage.py makemigrations
python manage.py migrate
```

### 5. Create Superuser
```bash
python manage.py createsuperuser
```

## Redis Setup (Required for WebSocket and Celery)

```bash
# Ubuntu/Debian
sudo apt install redis-server

# Start Redis
sudo systemctl start redis
sudo systemctl enable redis

# Test Redis
redis-cli ping  # Should return PONG
```

## Running the Application

### Development Server
```bash
# Activate virtual environment
source .venv/bin/activate

# Run with Daphne (ASGI server for WebSocket support)
daphne -b 0.0.0.0 -p 8000 config.asgi:application
```

### Celery Worker (for background tasks)
```bash
# In a separate terminal
source .venv/bin/activate
celery -A config worker -l info
```

### Celery Beat (for scheduled tasks)
```bash
# In another separate terminal
source .venv/bin/activate
celery -A config beat -l info
```

