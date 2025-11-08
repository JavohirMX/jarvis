"""
Serializers for AI Interactions API
"""
from rest_framework import serializers
from drf_spectacular.utils import extend_schema_field
from .models import Conversation, AIMessage, AIMemory


class AIMessageSerializer(serializers.ModelSerializer):
    """Serializer for AIMessage"""
    
    class Meta:
        model = AIMessage
        fields = ('id', 'role', 'content', 'context_data', 'ai_model_used',
                  'prompt_tokens', 'completion_tokens', 'total_tokens', 'created_at')
        read_only_fields = ('id', 'created_at')


class ConversationSerializer(serializers.ModelSerializer):
    """Serializer for Conversation"""
    messages = AIMessageSerializer(many=True, read_only=True)
    message_preview = serializers.SerializerMethodField()
    
    class Meta:
        model = Conversation
        fields = ('id', 'title', 'total_tokens_used', 'message_count',
                  'is_active', 'messages', 'message_preview', 'created_at', 'updated_at')
        read_only_fields = ('id', 'total_tokens_used', 'message_count', 'created_at', 'updated_at')
    
    @extend_schema_field(serializers.CharField(allow_null=True))
    def get_message_preview(self, obj) -> str | None:
        """Get last message preview"""
        last_msg = obj.messages.last()
        return last_msg.content[:100] if last_msg else None


class ConversationListSerializer(serializers.ModelSerializer):
    """Serializer for Conversation list (without messages)"""
    message_preview = serializers.SerializerMethodField()
    
    class Meta:
        model = Conversation
        fields = ('id', 'title', 'total_tokens_used', 'message_count',
                  'is_active', 'message_preview', 'created_at', 'updated_at')
        read_only_fields = ('id', 'total_tokens_used', 'message_count', 'created_at', 'updated_at')
    
    @extend_schema_field(serializers.CharField(allow_null=True))
    def get_message_preview(self, obj) -> str | None:
        last_msg = obj.messages.last()
        return last_msg.content[:100] if last_msg else None


class AIMemorySerializer(serializers.ModelSerializer):
    """Serializer for AIMemory"""
    
    class Meta:
        model = AIMemory
        fields = ('id', 'key_facts', 'created_at', 'updated_at')
        read_only_fields = ('id', 'created_at', 'updated_at')

