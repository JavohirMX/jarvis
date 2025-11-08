"""
Admin interface for voice commands
"""
from django.contrib import admin
from .models import VoiceCommand


@admin.register(VoiceCommand)
class VoiceCommandAdmin(admin.ModelAdmin):
    """Admin interface for VoiceCommand"""
    
    list_display = ('user', 'transcribed_preview', 'command_type', 'stt_method',
                    'audio_duration', 'total_cost', 'created_at')
    list_filter = ('command_type', 'stt_method', 'created_at')
    search_fields = ('user__username', 'transcribed_text', 'response_text')
    readonly_fields = ('created_at',)
    
    def transcribed_preview(self, obj):
        return obj.transcribed_text[:50]
    transcribed_preview.short_description = 'Transcribed Text'
