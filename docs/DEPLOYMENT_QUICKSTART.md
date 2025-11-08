# Quick Start: Deployment to DigitalOcean

This is a quick reference guide. For complete documentation, see [DEPLOYMENT.md](DEPLOYMENT.md).

## 📁 Files Created

All deployment files have been created:

```
✅ Dockerfile                      # Multi-stage build for Django app
✅ docker-compose.yml              # All services orchestration
✅ docker-entrypoint.sh            # Container startup script
✅ .dockerignore                   # Docker build exclusions
✅ nginx/jarvis.conf               # Nginx configuration with SSL
✅ .github/workflows/deploy.yml    # GitHub Actions CI/CD
✅ env.production.example          # Environment variables template
✅ deploy.sh                       # Manual deployment script
✅ DEPLOYMENT.md                   # Complete deployment guide
```

## 🚀 Quick Deployment Steps

### 1. Server Setup (One-Time)

SSH to your Droplet:
```bash
ssh jmx@your-droplet-ip

# Install Docker & Docker Compose
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh
sudo usermod -aG docker jmx
sudo apt install docker-compose -y

# Clone repository
mkdir -p /home/jmx/jarvis
cd /home/jmx/jarvis
git clone https://github.com/JavohirMX/jarvis.git .

# Create .env from template
cp env.production.example .env
nano .env  # Fill in all values

# Make scripts executable
chmod +x docker-entrypoint.sh deploy.sh
```

### 2. Nginx Setup

```bash
# Copy nginx config
sudo cp nginx/jarvis.conf /etc/nginx/sites-available/jarvis
sudo ln -s /etc/nginx/sites-available/jarvis /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx
```

### 3. SSL Certificate

```bash
# Install Certbot
sudo apt install certbot python3-certbot-nginx -y

# Get certificate (ensure DNS points to your Droplet first!)
sudo certbot certonly --nginx -d jarvis.javohirmx.com

# Restart Nginx
sudo systemctl restart nginx
```

### 4. Deploy Application

```bash
cd /home/jmx/jarvis
./deploy.sh
```

### 5. GitHub Actions Setup

Add these secrets to your GitHub repository (Settings → Secrets → Actions):

| Secret Name | Value |
|------------|-------|
| `DROPLET_HOST` | Your Droplet IP address |
| `DROPLET_USER` | `jmx` |
| `DROPLET_SSH_KEY` | Your private SSH key (entire content of `~/.ssh/id_rsa`) |

### 6. Verify Deployment

```bash
# Check containers
docker-compose ps

# Check logs
docker-compose logs -f web

# Test application
curl https://jarvis.javohirmx.com
```

## 🔧 Common Commands

```bash
# View logs
docker-compose logs -f

# Restart services
docker-compose restart

# Redeploy
./deploy.sh

# Stop all
docker-compose down

# Start all
docker-compose up -d
```

## 📝 Environment Variables Required

Edit `/home/jmx/jarvis/.env` and set:

```env
# Critical - Must Change
SECRET_KEY=generate-new-secret-key
DB_PASSWORD=strong-password
REDIS_PASSWORD=strong-password
OPENAI_API_KEY=sk-your-key

# Optional - Recommended to Change
MINIO_SECRET_KEY=strong-password
DJANGO_SUPERUSER_USERNAME=admin
DJANGO_SUPERUSER_PASSWORD=admin-password
DJANGO_SUPERUSER_EMAIL=admin@javohirmx.com
```

Generate SECRET_KEY:
```bash
python3 -c 'from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())'
```

## 🌐 Access Points

After deployment, access:

- **Application**: https://jarvis.javohirmx.com
- **Admin Panel**: https://jarvis.javohirmx.com/admin/
- **API Docs**: https://jarvis.javohirmx.com/api/docs/
- **WebSocket**: wss://jarvis.javohirmx.com/ws/assistant/
- **MinIO Console**: http://your-droplet-ip:9002

## 🔄 Automatic Deployments

Once GitHub Actions is configured:
1. Push to `main` branch
2. GitHub Actions automatically deploys
3. Monitor at: https://github.com/JavohirMX/jarvis/actions

## 📊 Architecture Overview

```
Internet (Port 443/80)
    ↓
Nginx (Reverse Proxy + SSL)
    ↓
Docker Network
    ├── Django/Daphne (Port 8080)
    ├── PostgreSQL (Port 5435)
    ├── Redis (Port 6380)
    ├── MinIO (Port 9001/9002)
    ├── Celery Worker
    └── Celery Beat
```

## ⚠️ Important Notes

1. **Before deploying**, ensure:
   - Domain `jarvis.javohirmx.com` points to your Droplet IP
   - All environment variables are set in `.env`
   - You have valid API keys

2. **Ports used**:
   - 8080: Django/Daphne
   - 5435: PostgreSQL
   - 6380: Redis
   - 9001: MinIO API
   - 9002: MinIO Console

3. **Data persistence**:
   - Database, Redis, MinIO, and static files are persisted in Docker volumes
   - To backup: `docker-compose exec db pg_dump ...`

## 🆘 Troubleshooting

**Containers won't start:**
```bash
docker-compose logs
docker-compose down -v
docker-compose up -d
```

**SSL issues:**
```bash
sudo certbot renew --force-renewal
sudo systemctl restart nginx
```

**GitHub Actions fails:**
- Check secrets are set correctly
- Verify SSH key has access to server
- Review workflow logs in GitHub

## 📚 Full Documentation

For complete details, troubleshooting, and advanced configuration:
- [DEPLOYMENT.md](DEPLOYMENT.md) - Complete deployment guide
- [README.md](README.md) - Application documentation

## ✅ Deployment Checklist

- [ ] Docker & Docker Compose installed on server
- [ ] Repository cloned to `/home/jmx/jarvis`
- [ ] `.env` file created and configured
- [ ] Nginx configuration copied and enabled
- [ ] SSL certificate obtained and installed
- [ ] GitHub Actions secrets configured
- [ ] First deployment completed successfully
- [ ] Application accessible at https://jarvis.javohirmx.com
- [ ] Admin panel accessible
- [ ] WebSocket connections working

---

**Status**: ✅ All deployment files created and ready!

**Next Steps**: Follow the deployment steps above to deploy your application.

**Support**: Check [DEPLOYMENT.md](DEPLOYMENT.md) for detailed troubleshooting.

