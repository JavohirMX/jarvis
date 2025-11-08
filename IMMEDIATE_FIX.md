# 🚨 IMMEDIATE FIX - MinIO Bucket Error

## The Error You're Seeing

```
NoSuchBucket: The specified bucket does not exist
```

## Quick Fix (Choose ONE)

### Option 1: Run Setup Command (FASTEST) ⚡

```bash
# SSH to your server
ssh user@your-server

# Navigate to project
cd /path/to/ai-assistant

# Run setup
docker-compose exec web python manage.py setup_minio
```

**Expected output:**
```
✓ Connected to MinIO
✓ Created bucket "jarvis-media"
✓ Set public read policy for avatars/ and chat_images/
✓ MinIO setup completed successfully!
```

**Done!** Try uploading an avatar now.

---

### Option 2: Restart with Auto-Setup

```bash
# Pull latest code (with the fix)
git pull

# Rebuild and restart
docker-compose down
docker-compose build web
docker-compose up -d

# Check logs to confirm bucket creation
docker-compose logs web | grep "MinIO"
```

**You should see:**
```
Waiting for MinIO...
MinIO is ready!
Setting up MinIO bucket...
✓ Bucket 'jarvis-media' already exists (or created)
```

---

### Option 3: Manual via MinIO Console

1. Go to: `http://your-server:9011`
2. Login: `minioadmin` / your-secret-key
3. Create Bucket: `jarvis-media`
4. Done!

---

## Test It Works

```bash
# Get your access token from login
TOKEN="your-token-here"

# Test avatar upload
curl -X PATCH http://your-server/api/profile/ \
  -H "Authorization: Bearer $TOKEN" \
  -F "avatar=@test.jpg"
```

**Success response:**
```json
{
  "avatar": "http://your-server:9010/jarvis-media/avatars/avatar_xxx.jpg",
  ...
}
```

---

## What Changed

I've updated your code to **automatically create the MinIO bucket** on startup:

- ✅ Updated `docker-entrypoint.sh` - Auto-creates bucket
- ✅ Created `setup_minio.py` - Manual setup command
- ✅ Added bucket policy - Public read for avatars

---

## Next Steps

1. **Immediate:** Run Option 1 to fix current deployment
2. **Future:** Pull latest code so future deployments auto-create bucket
3. **Verify:** Test avatar upload works

---

## Need Help?

Check the logs:
```bash
# Django logs
docker-compose logs web --tail 50

# MinIO logs  
docker-compose logs minio --tail 50
```

Run diagnostic:
```bash
docker-compose exec web python manage.py test_minio
```

---

**This should take < 2 minutes to fix!** 🚀

