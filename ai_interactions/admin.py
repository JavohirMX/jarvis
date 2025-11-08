"""
Admin interface for AI interactions
"""
from django.contrib import admin
from .models import Conversation, AIMessage, AIMemory


class AIMessageInline(admin.TabularInline):
    """Inline display of messages in conversation"""
    model = AIMessage
    extra = 0
    fields = ('role', 'content', 'total_tokens', 'created_at')
    readonly_fields = ('created_at',)


@admin.register(Conversation)
class ConversationAdmin(admin.ModelAdmin):
    """Admin interface for Conversation"""
    
    list_display = ('user', 'title', 'message_count', 'total_tokens_used', 'is_active', 'created_at')
    list_filter = ('is_active', 'created_at')
    search_fields = ('user__username', 'title')
    readonly_fields = ('created_at', 'updated_at')
    inlines = [AIMessageInline]
    
    fieldsets = (
        ('Basic Info', {
            'fields': ('user', 'title', 'is_active')
        }),
        ('Statistics', {
            'fields': ('message_count', 'total_tokens_used')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at')
        }),
    )


@admin.register(AIMessage)
class AIMessageAdmin(admin.ModelAdmin):
    """Admin interface for AIMessage"""
    
    list_display = ('conversation', 'role', 'content_preview', 'ai_model_used', 'total_tokens', 'created_at')
    list_filter = ('role', 'ai_model_used', 'created_at')
    search_fields = ('conversation__title', 'content')
    readonly_fields = ('created_at',)
    
    def content_preview(self, obj):
        return obj.content[:50]
    content_preview.short_description = 'Content'


@admin.register(AIMemory)
class AIMemoryAdmin(admin.ModelAdmin):
    """Admin interface for AIMemory"""
    
    list_display = ('user', 'created_at', 'updated_at')
    search_fields = ('user__username',)
    readonly_fields = ('created_at', 'updated_at')
