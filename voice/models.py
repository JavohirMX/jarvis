"""
Models for voice commands and speech processing
"""
from django.db import models
from django.contrib.auth.models import User
from decimal import Decimal


class VoiceCommand(models.Model):
    """Model to store voice commands and their processing"""
    
    COMMAND_TYPE_CHOICES = [
        ('question', 'Question'),
        ('action', 'Action'),
        ('translate', 'Translate'),
        ('summarize', 'Summarize'),
    ]
    
    STT_METHOD_CHOICES = [
        ('backend_whisper', 'Backend Whisper'),
        ('frontend_webspeech', 'Frontend Web Speech'),
        ('manual_text', 'Manual Text'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='voice_commands')
    audio_file_path = models.CharField(max_length=500, blank=True, null=True)
    transcribed_text = models.TextField()
    command_type = models.CharField(max_length=50, choices=COMMAND_TYPE_CHOICES)
    response_text = models.TextField(blank=True)
    stt_method = models.CharField(max_length=50, choices=STT_METHOD_CHOICES)
    
    # Token/duration tracking
    audio_duration = models.FloatField(null=True, blank=True)
    transcription_tokens = models.IntegerField(default=0)
    tts_characters = models.IntegerField(default=0)
    total_cost = models.DecimalField(max_digits=10, decimal_places=6, default=Decimal('0.0'))
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = 'Voice Command'
        verbose_name_plural = 'Voice Commands'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.user.username} - {self.transcribed_text[:50]}"
