"""
URL configuration for ai_interactions app
"""
from django.urls import path
from . import views

urlpatterns = [
    # Main AI endpoints
    path('chat/', views.AIChatView.as_view(), name='ai-chat'),
    path('summarize/', views.AISummarizeView.as_view(), name='ai-summarize'),
    path('translate/', views.AITranslateView.as_view(), name='ai-translate'),
    path('explain-code/', views.AIExplainCodeView.as_view(), name='ai-explain-code'),
    
    # Image upload for chat (WebSocket)
    path('upload-image/', views.UploadChatImageView.as_view(), name='upload-chat-image'),
    
    # Conversation management
    path('conversations/', views.ConversationListView.as_view(), name='conversation-list'),
    path('conversations/<int:pk>/', views.ConversationDetailView.as_view(), name='conversation-detail'),
    
    # Memory
    path('memory/', views.AIMemoryView.as_view(), name='ai-memory'),
]

