# MinIO Setup Guide

This guide explains how to configure MinIO object storage for user profile avatars and other media files.

## What is MinIO?

MinIO is a high-performance, S3-compatible object storage system. It's perfect for storing user-uploaded files like avatars, images, and other media.

## Prerequisites

- MinIO server running (can be local or remote)
- MinIO access credentials

## Installation

The required packages are already in `requirements.txt`:

```bash
pip install django-storages boto3
```

## Environment Configuration

Add the following variables to your `.env` file:

```bash
# MinIO Configuration
USE_MINIO=True
MINIO_ENDPOINT=http://localhost:9000
MINIO_ACCESS_KEY=minioadmin
MINIO_SECRET_KEY=minioadmin
MINIO_BUCKET_NAME=jarvis-media
MINIO_USE_SSL=False
MINIO_REGION=us-east-1

# Optional: Custom domain for direct access
# MINIO_CUSTOM_DOMAIN=cdn.yourdomain.com
```

### Configuration Variables Explained

| Variable | Description | Default | Required |
|----------|-------------|---------|----------|
| `USE_MINIO` | Enable/disable MinIO storage | `False` | Yes |
| `MINIO_ENDPOINT` | MinIO server URL | `http://localhost:9000` | Yes |
| `MINIO_ACCESS_KEY` | MinIO access key | `minioadmin` | Yes |
| `MINIO_SECRET_KEY` | MinIO secret key | `minioadmin` | Yes |
| `MINIO_BUCKET_NAME` | Bucket name for media files | `jarvis-media` | Yes |
| `MINIO_USE_SSL` | Use SSL/TLS connection | `False` | No |
| `MINIO_REGION` | AWS region (for compatibility) | `us-east-1` | No |
| `MINIO_CUSTOM_DOMAIN` | Custom CDN domain | None | No |

## Setting Up MinIO Server

### Option 1: Using Docker (Recommended for Development)

```bash
docker run -d \
  -p 9000:9000 \
  -p 9001:9001 \
  --name minio \
  -e "MINIO_ROOT_USER=minioadmin" \
  -e "MINIO_ROOT_PASSWORD=minioadmin" \
  -v /path/to/data:/data \
  minio/minio server /data --console-address ":9001"
```

Access the MinIO Console at: http://localhost:9001

### Option 2: Using Docker Compose

Create a `docker-compose.yml` file:

```yaml
version: '3.8'

services:
  minio:
    image: minio/minio:latest
    container_name: minio
    ports:
      - "9000:9000"
      - "9001:9001"
    environment:
      MINIO_ROOT_USER: minioadmin
      MINIO_ROOT_PASSWORD: minioadmin
    volumes:
      - minio_data:/data
    command: server /data --console-address ":9001"
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:9000/minio/health/live"]
      interval: 30s
      timeout: 20s
      retries: 3

volumes:
  minio_data:
```

Start MinIO:

```bash
docker-compose up -d
```

### Option 3: Standalone Binary

Download and install MinIO from: https://min.io/download

```bash
wget https://dl.min.io/server/minio/release/linux-amd64/minio
chmod +x minio
./minio server /data --console-address ":9001"
```

## Creating the Bucket

After starting MinIO:

1. Open the MinIO Console: http://localhost:9001
2. Login with your credentials (default: minioadmin/minioadmin)
3. Click "Buckets" → "Create Bucket"
4. Name it `jarvis-media` (or your configured bucket name)
5. Set the bucket policy to "public" if you want avatars to be publicly accessible

### Using MinIO Client (mc)

```bash
# Install mc
wget https://dl.min.io/client/mc/release/linux-amd64/mc
chmod +x mc

# Configure mc
./mc alias set myminio http://localhost:9000 minioadmin minioadmin

# Create bucket
./mc mb myminio/jarvis-media

# Set public read policy for avatars
./mc anonymous set download myminio/jarvis-media/avatars
```

## Testing the Configuration

### Test with Django Shell

```bash
python manage.py shell
```

```python
from django.core.files.base import ContentFile
from profiles.models import UserProfile
from django.contrib.auth.models import User

# Get or create a user
user = User.objects.first()
profile = user.profile

# Create a test file
test_file = ContentFile(b"test content", name="test.txt")

# Upload to MinIO
profile.avatar.save("test_avatar.jpg", test_file)

# Check the URL
print(profile.avatar.url)
# Should show MinIO URL like: http://localhost:9000/jarvis-media/avatars/test_avatar.jpg
```

## API Usage

### Upload Avatar

```bash
curl -X PATCH http://localhost:8000/api/profile/me/ \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -F "avatar=@/path/to/image.jpg"
```

### Get Profile with Avatar URL

```bash
curl -X GET http://localhost:8000/api/profile/me/ \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

Response:
```json
{
  "id": 1,
  "user": {
    "id": 1,
    "username": "testuser",
    "email": "test@example.com"
  },
  "avatar": "http://localhost:9000/jarvis-media/avatars/user_1/avatar_abc123.jpg",
  ...
}
```

## Storage Backend Details

The system uses two storage backends defined in `config/storages.py`:

### MinIOMediaStorage
- For public media files (avatars, images)
- ACL: `public-read`
- Files are publicly accessible via URL

### MinIOPrivateStorage
- For sensitive files
- ACL: `private`
- Requires signed URLs for access

## Switching Between Local and MinIO Storage

### Development (Local Storage)
```bash
USE_MINIO=False
```
Files stored in: `media/avatars/`

### Production (MinIO Storage)
```bash
USE_MINIO=True
MINIO_ENDPOINT=https://minio.yourdomain.com
MINIO_USE_SSL=True
```
Files stored in: MinIO bucket

## Production Considerations

1. **SSL/TLS**: Always use HTTPS in production
   ```bash
   MINIO_USE_SSL=True
   MINIO_ENDPOINT=https://minio.yourdomain.com
   ```

2. **CDN**: Use a custom domain with CDN
   ```bash
   MINIO_CUSTOM_DOMAIN=cdn.yourdomain.com
   ```

3. **Access Control**: Use proper IAM policies and rotate keys regularly

4. **Backup**: Configure MinIO bucket versioning and backup policies

5. **Monitoring**: Set up health checks and monitoring for MinIO server

## Troubleshooting

### Connection Errors

```python
# Check MinIO connectivity
import boto3
from django.conf import settings

s3 = boto3.client(
    's3',
    endpoint_url=settings.MINIO_ENDPOINT,
    aws_access_key_id=settings.MINIO_ACCESS_KEY,
    aws_secret_access_key=settings.MINIO_SECRET_KEY
)

# List buckets
print(s3.list_buckets())
```

### Bucket Not Found

Create the bucket manually or programmatically:

```python
s3.create_bucket(Bucket='jarvis-media')
```

### Permission Denied

1. Check MinIO credentials
2. Verify bucket policy allows read/write
3. Check MinIO server logs

### Files Not Accessible

1. Verify bucket policy is set to public for avatars
2. Check CORS settings in MinIO
3. Verify URL format in `MEDIA_URL` setting

## CORS Configuration

If accessing MinIO from a web frontend, configure CORS:

```bash
mc admin config set myminio api cors_allowed_origins="http://localhost:3000,http://localhost:8080"
mc admin service restart myminio
```

## Migration from Local to MinIO

If you already have files in local storage:

```python
# Migration script
from profiles.models import UserProfile
from django.core.files.base import ContentFile
import os

for profile in UserProfile.objects.filter(avatar__isnull=False):
    old_path = profile.avatar.path
    if os.path.exists(old_path):
        with open(old_path, 'rb') as f:
            content = f.read()
            profile.avatar.save(
                os.path.basename(old_path),
                ContentFile(content),
                save=True
            )
        print(f"Migrated avatar for {profile.user.username}")
```

## Additional Resources

- [MinIO Documentation](https://min.io/docs/minio/linux/index.html)
- [django-storages Documentation](https://django-storages.readthedocs.io/)
- [boto3 Documentation](https://boto3.amazonaws.com/v1/documentation/api/latest/index.html)

## Support

For issues or questions, refer to:
- MinIO Community: https://slack.min.io/
- django-storages Issues: https://github.com/jschneier/django-storages/issues

