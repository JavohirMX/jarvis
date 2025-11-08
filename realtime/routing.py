"""
WebSocket URL routing
"""
from django.urls import re_path
from . import consumers

websocket_urlpatterns = [
    re_path(r'ws/assistant/$', consumers.AIAssistantConsumer.as_asgi()),
]

