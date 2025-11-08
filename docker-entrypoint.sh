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

# Wait for MinIO to be ready (if enabled)
if [ "${USE_MINIO}" = "True" ]; then
  echo "Waiting for MinIO..."
  MINIO_HOST=$(echo ${MINIO_ENDPOINT} | sed 's~http[s]*://~~' | cut -d: -f1)
  MINIO_PORT=$(echo ${MINIO_ENDPOINT} | sed 's~http[s]*://~~' | cut -d: -f2)
  MINIO_PORT=${MINIO_PORT:-9000}
  
  until curl -f "http://${MINIO_HOST}:${MINIO_PORT}/minio/health/live" > /dev/null 2>&1; do
    echo "MinIO is unavailable - waiting..."
    sleep 2
  done
  echo "MinIO is ready!"
  
  # Create MinIO bucket if it doesn't exist
  echo "Setting up MinIO bucket..."
  python manage.py shell << END
import boto3
from botocore.exceptions import ClientError
import os

endpoint = os.getenv('MINIO_ENDPOINT', 'http://minio:9000')
access_key = os.getenv('MINIO_ACCESS_KEY', 'minioadmin')
secret_key = os.getenv('MINIO_SECRET_KEY', 'minioadmin')
bucket_name = os.getenv('MINIO_BUCKET_NAME', 'jarvis-media')

try:
    s3_client = boto3.client(
        's3',
        endpoint_url=endpoint,
        aws_access_key_id=access_key,
        aws_secret_access_key=secret_key,
        region_name='us-east-1',
        verify=False
    )
    
    # Check if bucket exists
    try:
        s3_client.head_bucket(Bucket=bucket_name)
        print(f"✓ Bucket '{bucket_name}' already exists")
    except ClientError:
        # Bucket doesn't exist, create it
        s3_client.create_bucket(Bucket=bucket_name)
        print(f"✓ Created bucket '{bucket_name}'")
        
        # Set bucket policy for public read access to avatars
        bucket_policy = {
            "Version": "2012-10-17",
            "Statement": [
                {
                    "Effect": "Allow",
                    "Principal": {"AWS": "*"},
                    "Action": ["s3:GetObject"],
                    "Resource": [f"arn:aws:s3:::{bucket_name}/avatars/*", f"arn:aws:s3:::{bucket_name}/chat_images/*"]
                }
            ]
        }
        
        import json
        s3_client.put_bucket_policy(Bucket=bucket_name, Policy=json.dumps(bucket_policy))
        print(f"✓ Set public read policy for avatars and chat_images")
        
except Exception as e:
    print(f"⚠ MinIO setup warning: {e}")
    print("You may need to create the bucket manually")
END
fi

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

