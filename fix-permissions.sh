#!/bin/bash
# Fix permissions for Docker bind mounts

set -e

echo "🔧 Fixing permissions for static files..."

cd /home/jmx/jarvis

# Create directories if they don't exist
mkdir -p staticfiles
mkdir -p media

# Get the current user's UID (should be 1000 for jmx)
USER_UID=$(id -u jmx)
USER_GID=$(id -g jmx)

echo "Setting ownership to UID:GID = $USER_UID:$USER_GID"

# Change ownership to match the user (UID 1000)
sudo chown -R $USER_UID:$USER_GID staticfiles
sudo chown -R $USER_UID:$USER_GID media

# Set proper permissions
chmod -R 755 staticfiles
chmod -R 755 media

echo "✅ Permissions fixed!"
echo ""
echo "Directory ownership:"
ls -ld staticfiles media

echo ""
echo "Now restart containers:"
echo "  docker-compose down"
echo "  docker-compose up -d"

