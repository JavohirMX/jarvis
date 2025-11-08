#!/bin/bash

# Deployment script for Jarvis AI Assistant
# This script can be run manually on the server for deployments

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored messages
print_message() {
    local color=$1
    local message=$2
    echo -e "${color}${message}${NC}"
}

# Check if running on the server
if [ ! -d "/home/jmx/jarvis" ]; then
    print_message "$RED" "❌ Error: This script should be run on the server at /home/jmx/jarvis"
    exit 1
fi

print_message "$BLUE" "🚀 Starting Jarvis AI Assistant deployment..."

# Navigate to project directory
cd /home/jmx/jarvis

# Check if .env exists
if [ ! -f ".env" ]; then
    print_message "$YELLOW" "⚠️  Warning: .env file not found!"
    print_message "$YELLOW" "Please create .env file from env.production.example"
    read -p "Do you want to continue? (y/n) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

# Pull latest changes from GitHub
print_message "$BLUE" "📥 Pulling latest code from GitHub..."
git fetch origin
git reset --hard origin/main

# Make scripts executable
chmod +x docker-entrypoint.sh
chmod +x deploy.sh

# Stop running containers
print_message "$BLUE" "🛑 Stopping existing containers..."
docker-compose down || true

# Build Docker images
print_message "$BLUE" "🏗️  Building Docker images..."
docker-compose build --no-cache

# Start containers
print_message "$BLUE" "🚢 Starting containers..."
docker-compose up -d

# Wait for services to start
print_message "$BLUE" "⏳ Waiting for services to be ready..."
sleep 20

# Check container status
print_message "$BLUE" "📊 Container status:"
docker-compose ps

# Check logs for errors
print_message "$BLUE" "📋 Recent logs:"
docker-compose logs --tail=50

# Health check
print_message "$BLUE" "🏥 Running health check..."
sleep 5

if curl -f http://localhost:8080/admin/login/ > /dev/null 2>&1; then
    print_message "$GREEN" "✅ Health check passed!"
else
    print_message "$RED" "❌ Health check failed!"
    print_message "$YELLOW" "Check logs with: docker-compose logs -f web"
    exit 1
fi

# Clean up old images
print_message "$BLUE" "🧹 Cleaning up old Docker images..."
docker image prune -f

print_message "$GREEN" "✅ Deployment completed successfully!"
print_message "$GREEN" "🌐 Application is running at: https://jarvis.javohirmx.com"

# Show helpful commands
print_message "$BLUE" "\n📝 Useful commands:"
echo "  - View logs: docker-compose logs -f"
echo "  - View specific service: docker-compose logs -f web"
echo "  - Restart services: docker-compose restart"
echo "  - Stop services: docker-compose down"
echo "  - Check status: docker-compose ps"

