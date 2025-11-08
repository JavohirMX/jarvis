# SSL Certificate Setup Guide

## The Problem

You're experiencing a chicken-and-egg problem:
- Nginx configuration references SSL certificates that don't exist yet
- Certbot can't obtain certificates because Nginx config test fails

## Solution: Two-Step Setup

### Step 1: Use HTTP-Only Configuration First

On your Droplet, run these commands:

```bash
# Navigate to project directory
cd /home/jmx/jarvis

# Remove the current broken symlink
sudo rm /etc/nginx/sites-enabled/jarvis

# Copy HTTP-only configuration (no SSL references)
sudo cp nginx/jarvis-http-only.conf /etc/nginx/sites-available/jarvis

# Create symlink
sudo ln -s /etc/nginx/sites-available/jarvis /etc/nginx/sites-enabled/

# Test configuration (should pass now)
sudo nginx -t

# If test passes, restart Nginx
sudo systemctl restart nginx
```

### Step 2: Obtain SSL Certificate

Now that Nginx is running without SSL errors:

```bash
# Create certbot directory
sudo mkdir -p /var/www/certbot
sudo chown -R www-data:www-data /var/www/certbot

# Obtain certificate using webroot method
sudo certbot certonly --webroot \
  -w /var/www/certbot \
  -d jarvis.javohirmx.com \
  --email your-email@example.com \
  --agree-tos \
  --no-eff-email

# Verify certificate was created
sudo ls -la /etc/letsencrypt/live/jarvis.javohirmx.com/
```

You should see:
- ✅ fullchain.pem
- ✅ privkey.pem
- ✅ chain.pem

### Step 3: Enable Full SSL Configuration

Now that certificates exist, enable the full configuration:

```bash
# Copy the full SSL configuration
sudo cp /home/jmx/jarvis/nginx/jarvis.conf /etc/nginx/sites-available/jarvis

# Test configuration (should pass now with certificates present)
sudo nginx -t

# If test passes, reload Nginx
sudo systemctl reload nginx
```

### Step 4: Verify HTTPS

```bash
# Test HTTPS locally
curl -I https://jarvis.javohirmx.com

# Test from browser
# Visit: https://jarvis.javohirmx.com
```

## Alternative Method: Standalone Mode

If the above doesn't work, try standalone mode (requires stopping Nginx temporarily):

```bash
# Stop Nginx temporarily
sudo systemctl stop nginx

# Obtain certificate in standalone mode
sudo certbot certonly --standalone \
  -d jarvis.javohirmx.com \
  --email your-email@example.com \
  --agree-tos \
  --no-eff-email

# Verify certificate
sudo ls -la /etc/letsencrypt/live/jarvis.javohirmx.com/

# Copy full SSL configuration
sudo cp /home/jmx/jarvis/nginx/jarvis.conf /etc/nginx/sites-available/jarvis

# Test and start Nginx
sudo nginx -t
sudo systemctl start nginx
```

## Troubleshooting

### Issue: DNS Not Propagated

**Error:** `Domain validation failed`

**Check DNS:**
```bash
# Check if DNS points to your Droplet
dig jarvis.javohirmx.com +short
nslookup jarvis.javohirmx.com
```

**Solution:** Wait for DNS propagation (can take up to 48 hours, usually much faster).

### Issue: Port 80 Not Accessible

**Check firewall:**
```bash
sudo ufw status
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp
```

**Check if port is listening:**
```bash
sudo netstat -tlnp | grep :80
```

### Issue: Nginx Test Still Fails

**View detailed error:**
```bash
sudo nginx -t 2>&1 | less
```

**Check Nginx error log:**
```bash
sudo tail -f /var/log/nginx/error.log
```

### Issue: Certificate Already Exists

**Renew/replace certificate:**
```bash
sudo certbot renew --force-renewal
```

## Automatic Renewal

Certbot automatically sets up renewal. Verify:

```bash
# Check renewal timer
sudo systemctl status certbot.timer

# Test renewal (dry run)
sudo certbot renew --dry-run

# Check renewal configuration
sudo cat /etc/cron.d/certbot
```

## Manual Renewal

If you need to renew manually:

```bash
sudo certbot renew
sudo systemctl reload nginx
```

## Certificate Information

View certificate details:

```bash
sudo certbot certificates
```

## Quick Reference

```bash
# Get certificate (webroot method)
sudo certbot certonly --webroot -w /var/www/certbot -d jarvis.javohirmx.com

# Get certificate (standalone method)
sudo systemctl stop nginx
sudo certbot certonly --standalone -d jarvis.javohirmx.com
sudo systemctl start nginx

# Test Nginx configuration
sudo nginx -t

# Reload Nginx (after config changes)
sudo systemctl reload nginx

# Restart Nginx (if reload doesn't work)
sudo systemctl restart nginx

# Check certificate expiry
sudo certbot certificates

# Renew all certificates
sudo certbot renew

# Renew specific certificate
sudo certbot renew --cert-name jarvis.javohirmx.com

# Test renewal
sudo certbot renew --dry-run
```

## Summary of Your Situation

Your current error indicates that you tried to use the full SSL configuration before obtaining certificates. Follow this exact order:

1. ✅ Use `jarvis-http-only.conf` (no SSL)
2. ✅ Obtain certificate with Certbot
3. ✅ Switch to `jarvis.conf` (with SSL)
4. ✅ Access https://jarvis.javohirmx.com

---

**Next Steps for You:**

Run these commands on your Droplet:

```bash
cd /home/jmx/jarvis
sudo rm /etc/nginx/sites-enabled/jarvis
sudo cp nginx/jarvis-http-only.conf /etc/nginx/sites-available/jarvis
sudo ln -s /etc/nginx/sites-available/jarvis /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx
sudo mkdir -p /var/www/certbot
sudo certbot certonly --webroot -w /var/www/certbot -d jarvis.javohirmx.com
sudo cp nginx/jarvis.conf /etc/nginx/sites-available/jarvis
sudo nginx -t
sudo systemctl reload nginx
```

That's it! 🎉

