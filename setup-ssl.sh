#!/bin/bash

# SSL Setup Script for Jarvis AI Assistant
# This script automates the SSL certificate setup process

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

print_message() {
    local color=$1
    local message=$2
    echo -e "${color}${message}${NC}"
}

print_message "$BLUE" "🔐 Starting SSL Certificate Setup for jarvis.javohirmx.com"

# Check if running as root
if [ "$EUID" -ne 0 ]; then 
    print_message "$RED" "❌ Please run as root or with sudo"
    exit 1
fi

# Confirm domain
read -p "Domain name [jarvis.javohirmx.com]: " DOMAIN
DOMAIN=${DOMAIN:-jarvis.javohirmx.com}

# Get email for Let's Encrypt
read -p "Email for Let's Encrypt notifications: " EMAIL
if [ -z "$EMAIL" ]; then
    print_message "$RED" "❌ Email is required"
    exit 1
fi

print_message "$BLUE" "📋 Configuration:"
echo "  Domain: $DOMAIN"
echo "  Email: $EMAIL"
echo ""
read -p "Continue? (y/n) " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    exit 1
fi

# Step 1: Setup HTTP-only Nginx configuration
print_message "$BLUE" "Step 1: Setting up HTTP-only Nginx configuration..."

# Remove existing symlink if present
if [ -L /etc/nginx/sites-enabled/jarvis ]; then
    rm /etc/nginx/sites-enabled/jarvis
    print_message "$YELLOW" "Removed existing symlink"
fi

# Copy HTTP-only configuration
cp /home/jmx/jarvis/nginx/jarvis-http-only.conf /etc/nginx/sites-available/jarvis
print_message "$GREEN" "✅ Copied HTTP-only configuration"

# Create symlink
ln -s /etc/nginx/sites-available/jarvis /etc/nginx/sites-enabled/
print_message "$GREEN" "✅ Created symlink"

# Test Nginx configuration
print_message "$BLUE" "Testing Nginx configuration..."
if nginx -t; then
    print_message "$GREEN" "✅ Nginx configuration test passed"
else
    print_message "$RED" "❌ Nginx configuration test failed"
    exit 1
fi

# Restart Nginx
systemctl restart nginx
print_message "$GREEN" "✅ Nginx restarted"

# Step 2: Create certbot directory
print_message "$BLUE" "Step 2: Preparing Certbot directory..."
mkdir -p /var/www/certbot
chown -R www-data:www-data /var/www/certbot
print_message "$GREEN" "✅ Certbot directory ready"

# Step 3: Obtain SSL certificate
print_message "$BLUE" "Step 3: Obtaining SSL certificate..."
print_message "$YELLOW" "This may take a minute..."

if certbot certonly --webroot \
    -w /var/www/certbot \
    -d "$DOMAIN" \
    --email "$EMAIL" \
    --agree-tos \
    --no-eff-email \
    --non-interactive; then
    print_message "$GREEN" "✅ SSL certificate obtained successfully"
else
    print_message "$RED" "❌ Failed to obtain SSL certificate"
    print_message "$YELLOW" "Trying standalone method..."
    
    # Try standalone method as fallback
    systemctl stop nginx
    
    if certbot certonly --standalone \
        -d "$DOMAIN" \
        --email "$EMAIL" \
        --agree-tos \
        --no-eff-email \
        --non-interactive; then
        print_message "$GREEN" "✅ SSL certificate obtained via standalone method"
    else
        print_message "$RED" "❌ Failed to obtain SSL certificate"
        print_message "$YELLOW" "Please check:"
        echo "  1. DNS is pointing to this server"
        echo "  2. Port 80 is accessible"
        echo "  3. Domain is correct"
        systemctl start nginx
        exit 1
    fi
fi

# Step 4: Verify certificate
print_message "$BLUE" "Step 4: Verifying certificate..."
if [ -f "/etc/letsencrypt/live/$DOMAIN/fullchain.pem" ]; then
    print_message "$GREEN" "✅ Certificate files found:"
    ls -la /etc/letsencrypt/live/$DOMAIN/
else
    print_message "$RED" "❌ Certificate files not found"
    exit 1
fi

# Step 5: Enable full SSL configuration
print_message "$BLUE" "Step 5: Enabling full SSL configuration..."

cp /home/jmx/jarvis/nginx/jarvis.conf /etc/nginx/sites-available/jarvis
print_message "$GREEN" "✅ Copied full SSL configuration"

# Test Nginx configuration
print_message "$BLUE" "Testing Nginx configuration with SSL..."
if nginx -t; then
    print_message "$GREEN" "✅ Nginx SSL configuration test passed"
else
    print_message "$RED" "❌ Nginx SSL configuration test failed"
    print_message "$YELLOW" "Reverting to HTTP-only configuration..."
    cp /home/jmx/jarvis/nginx/jarvis-http-only.conf /etc/nginx/sites-available/jarvis
    systemctl reload nginx
    exit 1
fi

# Reload Nginx
systemctl reload nginx
print_message "$GREEN" "✅ Nginx reloaded with SSL configuration"

# Step 6: Verify HTTPS
print_message "$BLUE" "Step 6: Verifying HTTPS..."
sleep 2

if curl -f -k -I https://localhost > /dev/null 2>&1; then
    print_message "$GREEN" "✅ HTTPS is working"
else
    print_message "$YELLOW" "⚠️  Could not verify HTTPS locally (this may be normal)"
fi

# Setup auto-renewal verification
print_message "$BLUE" "Checking certificate auto-renewal..."
if systemctl is-active --quiet certbot.timer; then
    print_message "$GREEN" "✅ Auto-renewal is enabled"
else
    print_message "$YELLOW" "⚠️  Auto-renewal timer not active"
fi

print_message "$GREEN" "
╔════════════════════════════════════════════════════════════╗
║                   ✅ SSL SETUP COMPLETE!                   ║
╚════════════════════════════════════════════════════════════╝
"

print_message "$GREEN" "🌐 Your site is now available at:"
echo "   https://$DOMAIN"
echo ""
print_message "$BLUE" "📋 Certificate Information:"
certbot certificates | grep -A 5 "$DOMAIN" || certbot certificates
echo ""
print_message "$BLUE" "🔄 Auto-renewal:"
echo "   Certificates will automatically renew before expiry"
echo "   Test renewal: sudo certbot renew --dry-run"
echo ""
print_message "$BLUE" "📝 Useful Commands:"
echo "   View certificates: sudo certbot certificates"
echo "   Manual renewal:    sudo certbot renew"
echo "   Check nginx:       sudo nginx -t"
echo "   Reload nginx:      sudo systemctl reload nginx"
echo ""
print_message "$GREEN" "All done! 🎉"

