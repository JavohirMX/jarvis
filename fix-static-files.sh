#!/bin/bash
# Fix static files for production deployment

set -e

cd /home/jmx/jarvis

echo "🔧 Fixing static files configuration..."

# Create directories if they don't exist
echo "📁 Creating directories..."
mkdir -p staticfiles
mkdir -p media

# Set proper permissions
echo "🔐 Setting permissions..."
chmod -R 755 staticfiles
chmod -R 755 media

# Remove old volumes if they exist
echo "🧹 Cleaning up old Docker volumes..."
docker-compose down
docker volume rm jarvis_static_volume 2>/dev/null || true
docker volume rm jarvis_media_volume 2>/dev/null || true

# Pull latest code
echo "📥 Pulling latest code..."
git pull origin main

# Rebuild containers
echo "🏗️ Rebuilding containers..."
docker-compose build web

# Start containers
echo "🚀 Starting containers..."
docker-compose up -d

# Wait for web service to be ready
echo "⏳ Waiting for web service..."
sleep 10

# Check if static files were collected
echo "📊 Checking static files..."
if [ -d "staticfiles/admin" ]; then
    echo "✅ Static files collected successfully!"
    ls -lh staticfiles/ | head -10
else
    echo "⚠️ Static files may not be collected yet, checking logs..."
    docker-compose logs web | tail -20
fi

# Test nginx configuration
echo "🔍 Testing Nginx configuration..."
if [ -f "/etc/nginx/sites-enabled/jarvis" ]; then
    sudo nginx -t && echo "✅ Nginx config is valid" || echo "⚠️ Nginx config has issues"
fi

# Show status
echo ""
echo "📋 Container status:"
docker-compose ps

echo ""
echo "✅ Done! Check your site at https://jarvis.javohirmx.com"
echo ""
echo "If CSS still doesn't load:"
echo "  1. Check: ls -la /home/jmx/jarvis/staticfiles/"
echo "  2. View logs: docker-compose logs web"
echo "  3. Restart Nginx: sudo systemctl restart nginx"

