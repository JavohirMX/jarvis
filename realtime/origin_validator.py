"""
Custom WebSocket origin validator to support desktop/mobile app protocols
"""
from channels.middleware import BaseMiddleware
from django.conf import settings


class CustomOriginValidator(BaseMiddleware):
    """
    Custom origin validator that allows:
    - Standard HTTP/HTTPS origins (via ALLOWED_HOSTS)
    - file:// protocol (for local file-based apps)
    - app:// protocol (for Electron/Tauri/mobile apps)
    """
    
    def __init__(self, application):
        super().__init__(application)
        # Additional allowed origin schemes
        self.allowed_schemes = ['file', 'app']
    
    def validate_origin(self, origin):
        """
        Validate the origin header.
        
        Returns True if:
        - Origin is None (some clients don't send origin)
        - Origin scheme is in allowed_schemes (file://, app://)
        - Origin matches ALLOWED_HOSTS (standard HTTP/HTTPS)
        """
        if origin is None:
            return True
        
        # Handle special schemes
        for scheme in self.allowed_schemes:
            if origin.startswith(f"{scheme}://"):
                return True
        
        # Validate HTTP/HTTPS origins against ALLOWED_HOSTS
        try:
            from urllib.parse import urlparse
            parsed = urlparse(origin)
            
            # Get the host from the origin
            host = parsed.hostname
            if parsed.port:
                host = f"{host}:{parsed.port}"
            
            # Check against ALLOWED_HOSTS
            allowed_hosts = settings.ALLOWED_HOSTS
            if '*' in allowed_hosts:
                return True
            
            # Check if host matches any allowed host
            for allowed_host in allowed_hosts:
                if allowed_host.startswith('.'):
                    # Wildcard subdomain match
                    if host.endswith(allowed_host) or host == allowed_host[1:]:
                        return True
                elif host == allowed_host:
                    return True
            
            return False
        except Exception:
            return False
    
    async def __call__(self, scope, receive, send):
        """
        Process the WebSocket connection with origin validation.
        """
        # Get origin from headers
        headers = dict(scope.get("headers", []))
        origin = None
        
        for header_name, header_value in headers.items():
            if header_name == b"origin":
                origin = header_value.decode("latin1")
                break
        
        # Validate origin
        if not self.validate_origin(origin):
            # Reject connection with 403 Forbidden
            await send({
                "type": "websocket.close",
                "code": 4403,
            })
            return
        
        # Origin is valid, continue to application
        return await super().__call__(scope, receive, send)

