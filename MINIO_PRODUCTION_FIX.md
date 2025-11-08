# MinIO Production Error Fix

## Problem

```
botocore.errorfactory.NoSuchBucket: The specified bucket does not exist
```

This error occurs when Django tries to upload files to MinIO but the bucket hasn't been created yet.

## Root Cause

The MinIO bucket `jarvis-media` was not created in the production environment during deployment.

## Solutions

### ✅ Solution 1: Auto-Create on Startup (RECOMMENDED)

The `docker-entrypoint.sh` has been updated to automatically create the MinIO bucket on container startup.

**What it does:**
- Waits for MinIO to be ready
- Creates `jarvis-media` bucket if it doesn't exist
- Sets public read policy for `avatars/` and `chat_images/` folders

**To apply:**
```bash
# Rebuild and restart the containers
docker-compose down
docker-compose build web
docker-compose up -d
```

The bucket will be created automatically on next startup!

### ✅ Solution 2: Manual Setup Command

Run this Django management command to setup MinIO manually:

```bash
# From host machine
docker-compose exec web python manage.py setup_minio

# Or SSH into server and run
cd /path/to/project
docker-compose exec web python manage.py setup_minio
```

**Output should show:**
```
Setting up MinIO...
Endpoint: http://minio:9000
Bucket: jarvis-media

✓ Connected to MinIO
✓ Created bucket "jarvis-media"
✓ Set public read policy for avatars/ and chat_images/
✓ Test file uploaded: test/.setup_test.txt
✓ Test file deleted

============================================================
✓ MinIO setup completed successfully!
============================================================
```

### ✅ Solution 3: Using MinIO Console (Manual)

1. **Access MinIO Console:**
   ```
   http://your-server:9011
   ```

2. **Login with credentials:**
   - Username: `minioadmin` (or your `MINIO_ACCESS_KEY`)
   - Password: `minioadmin` (or your `MINIO_SECRET_KEY`)

3. **Create Bucket:**
   - Click "Buckets" → "Create Bucket"
   - Name: `jarvis-media`
   - Click "Create"

4. **Set Public Read Policy:**
   - Go to bucket → "Access" tab
   - Set policy to allow public read for `avatars/*` and `chat_images/*`

### ✅ Solution 4: Using MinIO Client (mc)

```bash
# Install mc
wget https://dl.min.io/client/mc/release/linux-amd64/mc
chmod +x mc

# Configure
./mc alias set myprod http://your-server:9010 minioadmin your-secret-key

# Create bucket
./mc mb myprod/jarvis-media

# Set public read policy for avatars
./mc anonymous set download myprod/jarvis-media/avatars

# Set public read policy for chat images
./mc anonymous set download myprod/jarvis-media/chat_images

# Verify
./mc ls myprod
```

## Verification

After applying any solution, test the avatar upload:

```bash
# Get access token (via login endpoint)
TOKEN="your-access-token"

# Upload avatar
curl -X PATCH https://your-domain.com/api/profile/ \
  -H "Authorization: Bearer $TOKEN" \
  -F "avatar=@test.jpg"

# Should return:
{
  "avatar": "http://your-server:9010/jarvis-media/avatars/avatar_xxx.jpg",
  ...
}
```

## Files Modified

1. **`docker-entrypoint.sh`** - Added automatic MinIO bucket creation
2. **`profiles/management/commands/setup_minio.py`** - New management command

## Environment Variables Required

Ensure these are set in your `.env` or production environment:

```bash
USE_MINIO=True
MINIO_ENDPOINT=http://minio:9000
MINIO_ACCESS_KEY=your_access_key
MINIO_SECRET_KEY=your_secret_key
MINIO_BUCKET_NAME=jarvis-media
MINIO_USE_SSL=False
MINIO_REGION=us-east-1
```

## Quick Fix (If Already Deployed)

If your containers are already running and you need a quick fix:

```bash
# Method 1: Run setup command
docker-compose exec web python manage.py setup_minio

# Method 2: Restart with auto-setup
docker-compose restart web
```

## Prevention

The updated `docker-entrypoint.sh` will prevent this issue in future deployments by:
- ✅ Waiting for MinIO to be ready
- ✅ Auto-creating the bucket if missing
- ✅ Setting proper public read policies
- ✅ Running before Django starts accepting requests

## Troubleshooting

### MinIO Not Accessible

```bash
# Check if MinIO is running
docker-compose ps minio

# Check MinIO logs
docker-compose logs minio

# Check MinIO health
curl http://localhost:9010/minio/health/live
```

### Bucket Still Not Found

```bash
# Verify bucket exists
docker-compose exec web python manage.py shell
>>> from config.minio_service import get_minio_service
>>> minio = get_minio_service()
>>> minio.ensure_bucket_exists('jarvis-media')
```

### Permission Errors

```bash
# Check MinIO credentials in .env
grep MINIO .env

# Verify credentials work
docker-compose exec web python manage.py test_minio
```

## Related Files

- `docker-entrypoint.sh` - Startup script with MinIO setup
- `profiles/management/commands/setup_minio.py` - Manual setup command
- `profiles/management/commands/test_minio.py` - Test MinIO connection
- `config/storages.py` - Django storage backends
- `config/minio_service.py` - Direct MinIO operations

## Status

✅ **Fixed** - Bucket is now auto-created on deployment  
✅ **Tested** - Manual setup command works  
✅ **Documented** - Complete troubleshooting guide  

---

**Last Updated:** November 8, 2025  
**Issue:** `NoSuchBucket` error in production  
**Resolution:** Auto-create bucket on startup + manual command

