"""
Serializers for Voice API
"""
from rest_framework import serializers
from .models import VoiceCommand


class VoiceCommandSerializer(serializers.ModelSerializer):
    """Serializer for VoiceCommand"""
    
    class Meta:
        model = VoiceCommand
        fields = ('id', 'transcribed_text', 'command_type', 'response_text',
                  'stt_method', 'audio_duration', 'transcription_tokens',
                  'tts_characters', 'total_cost', 'created_at')
        read_only_fields = ('id', 'created_at')

