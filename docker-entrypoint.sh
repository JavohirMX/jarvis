#!/bin/bash
set -e

echo "Starting Django application..."

# Wait for PostgreSQL to be ready
echo "Waiting for PostgreSQL..."
until python << END
import sys
import psycopg2
try:
    conn = psycopg2.connect(
        dbname="${DB_NAME:-ai_assistant}",
        user="${DB_USER:-ai_assistant_user}",
        password="${DB_PASSWORD}",
        host="${DB_HOST:-db}",
        port="${DB_PORT:-5432}"
    )
    conn.close()
except psycopg2.OperationalError:
    sys.exit(1)
END
do
  echo "PostgreSQL is unavailable - waiting..."
  sleep 1
done
echo "PostgreSQL is ready!"

# Wait for Redis to be ready
echo "Waiting for Redis..."
until python << END
import sys
import redis
try:
    r = redis.Redis(
        host="${REDIS_HOST:-redis}",
        port=int("${REDIS_PORT:-6379}"),
        password="${REDIS_PASSWORD}",
        socket_connect_timeout=2
    )
    r.ping()
except (redis.ConnectionError, redis.TimeoutError):
    sys.exit(1)
END
do
  echo "Redis is unavailable - waiting..."
  sleep 1
done
echo "Redis is ready!"

# Run database migrations
echo "Running database migrations..."
python manage.py migrate --noinput

# Collect static files
echo "Collecting static files..."
python manage.py collectstatic --noinput --clear

# Create superuser if it doesn't exist (optional, for first deployment)
if [ "$DJANGO_SUPERUSER_USERNAME" ] && [ "$DJANGO_SUPERUSER_PASSWORD" ] && [ "$DJANGO_SUPERUSER_EMAIL" ]; then
    echo "Creating superuser..."
    python manage.py shell << END
from django.contrib.auth import get_user_model
User = get_user_model()
if not User.objects.filter(username='$DJANGO_SUPERUSER_USERNAME').exists():
    User.objects.create_superuser('$DJANGO_SUPERUSER_USERNAME', '$DJANGO_SUPERUSER_EMAIL', '$DJANGO_SUPERUSER_PASSWORD')
    print('Superuser created successfully')
else:
    print('Superuser already exists')
END
fi

echo "Starting application server..."
exec "$@"

