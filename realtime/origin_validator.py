"""
Custom WebSocket origin validator to support desktop/mobile app protocols
"""
from channels.security.websocket import OriginValidator


class CustomOriginValidator(OriginValidator):
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
        - Origin scheme is in allowed_schemes (file://, app://)
        - Origin is in ALLOWED_HOSTS (standard HTTP/HTTPS)
        """
        if origin is None:
            return True
        
        # Parse the origin
        try:
            # Handle special schemes
            for scheme in self.allowed_schemes:
                if origin.startswith(f"{scheme}://"):
                    return True
            
            # Fall back to standard validation for HTTP/HTTPS
            return super().validate_origin(origin)
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
        return await self.application(scope, receive, send)

