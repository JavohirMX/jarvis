"""
URL configuration for voice app
"""
from django.urls import path
from . import views

urlpatterns = [
    path('history/', views.VoiceHistoryView.as_view(), name='voice-history'),
]

