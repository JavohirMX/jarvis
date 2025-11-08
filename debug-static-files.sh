#!/bin/bash
# Debug static files issue in production

echo "=== Debugging Static Files Issue ==="
echo ""

echo "1. Checking if staticfiles directory exists:"
ls -la /home/jmx/jarvis/staticfiles/
echo ""

echo "2. Checking ownership and permissions:"
ls -ld /home/jmx/jarvis/staticfiles
echo ""

echo "3. Checking if static files were collected:"
if [ -d "/home/jmx/jarvis/staticfiles/admin" ]; then
    echo "✅ Admin static files found"
    ls -la /home/jmx/jarvis/staticfiles/admin/ | head -5
else
    echo "❌ Admin static files NOT found"
fi
echo ""

if [ -d "/home/jmx/jarvis/staticfiles/css" ]; then
    echo "✅ CSS directory found"
    ls -la /home/jmx/jarvis/staticfiles/css/
else
    echo "❌ CSS directory NOT found"
fi
echo ""

echo "4. Checking container logs for collectstatic:"
docker-compose logs web 2>&1 | grep -i "static" | tail -10
echo ""

echo "5. Testing static file access from host:"
if [ -f "/home/jmx/jarvis/staticfiles/admin/css/base.css" ]; then
    echo "✅ Can access admin CSS from host"
    ls -lh /home/jmx/jarvis/staticfiles/admin/css/base.css
else
    echo "❌ Cannot access admin CSS from host"
fi
echo ""

echo "6. Checking Nginx configuration:"
if [ -f "/etc/nginx/sites-enabled/jarvis" ]; then
    echo "✅ Nginx config exists"
    grep -A 3 "location /static/" /etc/nginx/sites-enabled/jarvis
else
    echo "❌ Nginx config NOT found"
fi
echo ""

echo "7. Testing Nginx static file serving:"
curl -I http://localhost/static/admin/css/base.css 2>&1 | head -5
echo ""

echo "8. Checking Nginx error logs:"
sudo tail -20 /var/log/nginx/jarvis_error.log 2>/dev/null || echo "No errors found"
echo ""

echo "9. Container status:"
docker-compose ps web
echo ""

echo "=== Recommendations ==="
echo ""
echo "If static files are missing:"
echo "  docker-compose exec web python manage.py collectstatic --noinput"
echo ""
echo "If permissions are wrong:"
echo "  sudo chown -R jmx:jmx /home/jmx/jarvis/staticfiles"
echo "  chmod -R 755 /home/jmx/jarvis/staticfiles"
echo ""
echo "If Nginx can't find files:"
echo "  sudo nginx -t"
echo "  sudo systemctl restart nginx"
echo ""
echo "Check browser console (F12) for specific 404 errors"

