# Deployment Guide for Jarvis AI Assistant

Complete guide for deploying the Django AI Assistant to DigitalOcean using Docker and GitHub Actions.

## Table of Contents
1. [Prerequisites](#prerequisites)
2. [Server Setup](#server-setup)
3. [GitHub Configuration](#github-configuration)
4. [Initial Deployment](#initial-deployment)
5. [SSL Certificate Setup](#ssl-certificate-setup)
6. [Nginx Configuration](#nginx-configuration)
7. [Automatic Deployments](#automatic-deployments)
8. [Monitoring & Maintenance](#monitoring--maintenance)
9. [Troubleshooting](#troubleshooting)

---

## Prerequisites

### Local Requirements
- Git installed
- Access to GitHub repository: https://github.com/JavohirMX/jarvis
- SSH access to DigitalOcean Droplet

### Server Requirements
- DigitalOcean Droplet (Ubuntu 20.04+ recommended)
- Docker and Docker Compose installed
- Nginx installed and configured
- Domain: jarvis.javohirmx.com pointing to Droplet IP
- Minimum 2GB RAM recommended

### Required Credentials
- OpenAI API Key
- Anthropic API Key (optional)
- Gemini API Key (optional)
- Database passwords
- Redis password

---

## Server Setup

### 1. Install Docker and Docker Compose

SSH into your Droplet:
```bash
ssh jmx@your-droplet-ip
```

Install Docker:
```bash
# Update packages
sudo apt update
sudo apt upgrade -y

# Install Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh

# Add user to docker group
sudo usermod -aG docker jmx
newgrp docker

# Install Docker Compose
sudo apt install docker-compose -y

# Verify installation
docker --version
docker-compose --version
```

### 2. Create Project Directory

```bash
# Create project directory
mkdir -p /home/jmx/jarvis
cd /home/jmx/jarvis

# Clone repository
git clone https://github.com/JavohirMX/jarvis.git .

# Or if already cloned, pull latest
git pull origin main
```

### 3. Configure Environment Variables

Create `.env` file from template:
```bash
cp env.production.example .env
nano .env
```

Fill in all required values:
```env
# Django
DEBUG=False
SECRET_KEY=your-super-secret-key-here-change-this
ALLOWED_HOSTS=jarvis.javohirmx.com,localhost,127.0.0.1

# Database
DB_NAME=ai_assistant
DB_USER=ai_assistant_user
DB_PASSWORD=your-secure-database-password-here

# Redis
REDIS_PASSWORD=your-secure-redis-password-here

# MinIO
MINIO_SECRET_KEY=change-this-secure-password

# AI API Keys
OPENAI_API_KEY=sk-your-openai-api-key-here
ANTHROPIC_API_KEY=sk-ant-your-anthropic-api-key-here
GEMINI_API_KEY=your-gemini-api-key-here

# Optional: Create superuser on first deployment
DJANGO_SUPERUSER_USERNAME=admin
DJANGO_SUPERUSER_PASSWORD=your-admin-password
DJANGO_SUPERUSER_EMAIL=admin@javohirmx.com
```

**Important:** Generate a secure `SECRET_KEY`:
```bash
python3 -c 'from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())'
```

### 4. Make Scripts Executable

```bash
chmod +x docker-entrypoint.sh
chmod +x deploy.sh
```

---

## Nginx Configuration

### 1. Copy Nginx Configuration

```bash
# Copy nginx config
sudo cp /home/jmx/jarvis/nginx/jarvis.conf /etc/nginx/sites-available/jarvis

# Create symlink (if not already active)
sudo ln -s /etc/nginx/sites-available/jarvis /etc/nginx/sites-enabled/

# Test nginx configuration
sudo nginx -t
```

### 2. Create Certbot Directory

```bash
sudo mkdir -p /var/www/certbot
sudo chown -R www-data:www-data /var/www/certbot
```

### 3. Restart Nginx

```bash
sudo systemctl restart nginx
sudo systemctl status nginx
```

---

## SSL Certificate Setup

### 1. Install Certbot

```bash
sudo apt install certbot python3-certbot-nginx -y
```

### 2. Obtain SSL Certificate

Make sure your domain `jarvis.javohirmx.com` points to your Droplet IP first!

```bash
# Obtain certificate
sudo certbot certonly --nginx -d jarvis.javohirmx.com

# Or use webroot method
sudo certbot certonly --webroot -w /var/www/certbot -d jarvis.javohirmx.com
```

Follow the prompts and provide your email address.

### 3. Verify SSL Certificate

```bash
sudo ls -la /etc/letsencrypt/live/jarvis.javohirmx.com/
```

You should see:
- `fullchain.pem`
- `privkey.pem`
- `chain.pem`

### 4. Restart Nginx

```bash
sudo systemctl restart nginx
```

### 5. Auto-Renewal Setup

Certbot automatically sets up renewal. Verify with:
```bash
sudo systemctl status certbot.timer
sudo certbot renew --dry-run
```

---

## Initial Deployment

### Option 1: Using Deploy Script (Recommended)

```bash
cd /home/jmx/jarvis
./deploy.sh
```

This script will:
- Pull latest code
- Build Docker images
- Start all containers
- Run migrations
- Collect static files
- Perform health check

### Option 2: Manual Deployment

```bash
cd /home/jmx/jarvis

# Build and start containers
docker-compose build
docker-compose up -d

# Check status
docker-compose ps

# View logs
docker-compose logs -f
```

### Verify Deployment

1. **Check containers are running:**
   ```bash
   docker-compose ps
   ```
   All services should show "Up" status.

2. **Check application logs:**
   ```bash
   docker-compose logs -f web
   ```

3. **Access the application:**
   - HTTP: http://jarvis.javohirmx.com (should redirect to HTTPS)
   - HTTPS: https://jarvis.javohirmx.com
   - Admin: https://jarvis.javohirmx.com/admin/
   - API Docs: https://jarvis.javohirmx.com/api/docs/

4. **MinIO Console (optional):**
   - http://your-droplet-ip:9002

---

## GitHub Configuration

### 1. Add GitHub Secrets

Go to your repository: https://github.com/JavohirMX/jarvis

Navigate to: **Settings** → **Secrets and variables** → **Actions** → **New repository secret**

Add the following secrets:

#### Required Secrets:

1. **DROPLET_HOST**
   - Value: Your Droplet's IP address (e.g., `164.92.123.45`)

2. **DROPLET_USER**
   - Value: `jmx`

3. **DROPLET_SSH_KEY**
   - Value: Your private SSH key that has access to the Droplet
   - To get your private key:
     ```bash
     cat ~/.ssh/id_rsa
     ```
   - Copy the entire content including `-----BEGIN OPENSSH PRIVATE KEY-----` and `-----END OPENSSH PRIVATE KEY-----`

### 2. Generate SSH Key (If Needed)

If you don't have an SSH key on your Droplet:

```bash
# On your local machine
ssh-keygen -t rsa -b 4096 -C "github-actions@jarvis"

# Copy public key to server
ssh-copy-id -i ~/.ssh/id_rsa.pub jmx@your-droplet-ip

# Test connection
ssh jmx@your-droplet-ip
```

### 3. Verify GitHub Actions

Push a commit to the `main` branch:
```bash
git add .
git commit -m "Setup deployment"
git push origin main
```

Check the workflow:
- Go to **Actions** tab in GitHub
- You should see the workflow running
- Monitor the deployment progress

---

## Automatic Deployments

With GitHub Actions configured, deployments happen automatically:

1. **On every push to `main` branch:**
   - GitHub Actions workflow triggers
   - Code is pulled on the server
   - Docker images are rebuilt
   - Containers are restarted
   - Health check is performed

2. **Manual deployment:**
   - Go to **Actions** tab
   - Select "Deploy to DigitalOcean" workflow
   - Click "Run workflow"

3. **Local manual deployment:**
   ```bash
   ssh jmx@your-droplet-ip
   cd /home/jmx/jarvis
   ./deploy.sh
   ```

---

## Monitoring & Maintenance

### View Logs

```bash
# All services
docker-compose logs -f

# Specific service
docker-compose logs -f web
docker-compose logs -f db
docker-compose logs -f redis
docker-compose logs -f celery_worker

# Last 100 lines
docker-compose logs --tail=100

# Nginx logs
sudo tail -f /var/log/nginx/jarvis_access.log
sudo tail -f /var/log/nginx/jarvis_error.log
```

### Check Container Status

```bash
docker-compose ps
docker stats
```

### Restart Services

```bash
# Restart all
docker-compose restart

# Restart specific service
docker-compose restart web
docker-compose restart celery_worker

# Restart nginx
sudo systemctl restart nginx
```

### Database Backup

```bash
# Backup database
docker-compose exec db pg_dump -U ai_assistant_user ai_assistant > backup_$(date +%Y%m%d).sql

# Restore database
cat backup_20241108.sql | docker-compose exec -T db psql -U ai_assistant_user ai_assistant
```

### Update Dependencies

```bash
cd /home/jmx/jarvis

# Pull latest code
git pull origin main

# Rebuild containers
docker-compose build --no-cache

# Restart
docker-compose down
docker-compose up -d
```

### Clean Up Docker Resources

```bash
# Remove unused images
docker image prune -f

# Remove unused volumes
docker volume prune -f

# Remove unused containers
docker container prune -f

# Complete cleanup (be careful!)
docker system prune -af
```

---

## Troubleshooting

### 1. Containers Won't Start

**Check logs:**
```bash
docker-compose logs web
```

**Common issues:**
- Missing environment variables in `.env`
- Database connection issues
- Port conflicts

**Solution:**
```bash
# Stop all containers
docker-compose down

# Check for port conflicts
sudo lsof -i :8080
sudo lsof -i :5435

# Restart
docker-compose up -d
```

### 2. Database Connection Error

**Check database is running:**
```bash
docker-compose ps db
docker-compose logs db
```

**Test connection:**
```bash
docker-compose exec db psql -U ai_assistant_user -d ai_assistant
```

**Reset database (careful!):**
```bash
docker-compose down -v
docker-compose up -d
```

### 3. Static Files Not Loading

**Collect static files manually:**
```bash
docker-compose exec web python manage.py collectstatic --noinput
```

**Check Nginx configuration:**
```bash
sudo nginx -t
sudo systemctl restart nginx
```

**Check permissions:**
```bash
ls -la /home/jmx/jarvis/staticfiles/
```

### 4. SSL Certificate Issues

**Verify certificate:**
```bash
sudo certbot certificates
```

**Renew manually:**
```bash
sudo certbot renew --force-renewal
sudo systemctl restart nginx
```

**Check nginx SSL config:**
```bash
sudo nano /etc/nginx/sites-available/jarvis
```

### 5. WebSocket Connection Failed

**Check nginx WebSocket configuration:**
```bash
grep -A 10 "location /ws/" /etc/nginx/sites-available/jarvis
```

**Check Daphne logs:**
```bash
docker-compose logs -f web | grep -i websocket
```

**Test WebSocket connection:**
```bash
wscat -c wss://jarvis.javohirmx.com/ws/assistant/
```

### 6. High Memory Usage

**Check container resources:**
```bash
docker stats
```

**Restart memory-hungry services:**
```bash
docker-compose restart celery_worker
docker-compose restart web
```

**Increase server resources if needed.**

### 7. GitHub Actions Deployment Fails

**Check workflow logs:**
- Go to GitHub → Actions tab
- Click on failed workflow
- Review error messages

**Common issues:**
- SSH key incorrect or missing
- Server not accessible
- Docker build failures

**Test SSH connection manually:**
```bash
ssh -i ~/.ssh/id_rsa jmx@your-droplet-ip
```

### 8. Permission Denied Errors

**Fix permissions:**
```bash
sudo chown -R jmx:jmx /home/jmx/jarvis
chmod +x /home/jmx/jarvis/docker-entrypoint.sh
chmod +x /home/jmx/jarvis/deploy.sh
```

---

## Health Checks

### Application Health

```bash
# HTTP health check
curl -f http://localhost:8080/admin/login/

# HTTPS health check
curl -f https://jarvis.javohirmx.com/admin/login/
```

### Service Health

```bash
# Check all services
docker-compose ps

# Individual health checks
docker-compose exec web python manage.py check
docker-compose exec db pg_isready
docker-compose exec redis redis-cli ping
```

---

## Security Best Practices

1. **Keep secrets secure:**
   - Never commit `.env` file
   - Use strong passwords
   - Rotate API keys regularly

2. **Update regularly:**
   ```bash
   sudo apt update && sudo apt upgrade -y
   docker-compose pull
   docker-compose up -d
   ```

3. **Monitor logs:**
   - Check for suspicious activity
   - Monitor error logs
   - Set up alerts (Sentry, etc.)

4. **Firewall configuration:**
   ```bash
   sudo ufw enable
   sudo ufw allow 22/tcp      # SSH
   sudo ufw allow 80/tcp      # HTTP
   sudo ufw allow 443/tcp     # HTTPS
   sudo ufw status
   ```

5. **Backup regularly:**
   - Database backups
   - Environment files
   - Docker volumes

---

## Production Checklist

Before going live, verify:

- [ ] Domain points to Droplet IP
- [ ] SSL certificate installed and working
- [ ] All environment variables set in `.env`
- [ ] `DEBUG=False` in production
- [ ] Strong `SECRET_KEY` generated
- [ ] Database password is secure
- [ ] Redis password is secure
- [ ] GitHub Actions secrets configured
- [ ] Nginx configuration tested
- [ ] Firewall configured
- [ ] Backups configured
- [ ] Monitoring/logging set up
- [ ] Health checks passing
- [ ] All containers running
- [ ] Static files serving correctly
- [ ] WebSocket connections working
- [ ] Admin panel accessible
- [ ] API documentation accessible

---

## Useful Commands Reference

```bash
# Deployment
./deploy.sh                              # Deploy with script
docker-compose up -d                     # Start services
docker-compose down                      # Stop services
docker-compose restart                   # Restart all
docker-compose build --no-cache         # Rebuild images

# Logs
docker-compose logs -f                   # All logs
docker-compose logs -f web              # Web service logs
sudo tail -f /var/log/nginx/jarvis_error.log  # Nginx logs

# Database
docker-compose exec db psql -U ai_assistant_user ai_assistant
docker-compose exec web python manage.py migrate
docker-compose exec web python manage.py createsuperuser

# Maintenance
docker image prune -f                    # Clean images
docker volume prune -f                   # Clean volumes
docker system prune -af                  # Clean everything

# Nginx
sudo nginx -t                            # Test config
sudo systemctl restart nginx             # Restart
sudo systemctl status nginx              # Check status

# SSL
sudo certbot renew                       # Renew certificates
sudo certbot certificates                # List certificates
```

---

## Support

For issues or questions:
- Check logs first
- Review troubleshooting section
- Check GitHub Issues
- Contact: admin@javohirmx.com

---

## Version History

- **v1.0** (2024-11-08): Initial deployment setup with Docker, GitHub Actions, and SSL

---

**Deployment Guide Complete! 🚀**

Your Django AI Assistant is now ready for production deployment on DigitalOcean at https://jarvis.javohirmx.com

