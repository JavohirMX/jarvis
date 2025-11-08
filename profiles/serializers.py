"""
Serializers for UserProfile API
"""
from rest_framework import serializers
from django.contrib.auth.models import User
from drf_spectacular.utils import extend_schema_field
from .models import UserProfile


class ProfileUserSerializer(serializers.ModelSerializer):
    """Serializer for User model (basic info only)"""
    class Meta:
        model = User
        fields = ('id', 'username', 'email')
        read_only_fields = ('id', 'username', 'email')


class UserProfileSerializer(serializers.ModelSerializer):
    """Serializer for UserProfile with all settings"""
    user = ProfileUserSerializer(read_only=True)
    daily_remaining = serializers.SerializerMethodField()
    monthly_remaining = serializers.SerializerMethodField()
    
    class Meta:
        model = UserProfile
        fields = (
            'id',
            'user',
            # Profile information
            'avatar',
            # Theme preferences
            'theme',
            'theme_custom_colors',
            # AI settings
            'ai_response_length',
            # Notification settings
            'notifications_enabled',
            'notification_sound',
            'notification_position',
            # Window preferences
            'window_default_x',
            'window_default_y',
            'window_default_width',
            'window_default_height',
            'window_opacity',
            # Voice settings
            'voice_enabled',
            'preferred_voice',
            'voice_speed',
            'voice_language',
            # Token usage (read-only)
            'total_tokens_used',
            'current_month_tokens',
            'current_day_tokens',
            'daily_token_limit',
            'monthly_token_limit',
            'daily_remaining',
            'monthly_remaining',
            'is_premium_user',
            # Timestamps
            'created_at',
            'updated_at',
        )
        read_only_fields = (
            'id',
            'user',
            'total_tokens_used',
            'current_month_tokens',
            'current_day_tokens',
            'daily_token_limit',
            'monthly_token_limit',
            'is_premium_user',
            'created_at',
            'updated_at',
            'daily_remaining',
            'monthly_remaining',
        )
    
    @extend_schema_field(serializers.IntegerField())
    def get_daily_remaining(self, obj) -> int:
        """Calculate remaining daily tokens"""
        return obj.daily_tokens_remaining()
    
    @extend_schema_field(serializers.IntegerField())
    def get_monthly_remaining(self, obj) -> int:
        """Calculate remaining monthly tokens"""
        return obj.monthly_tokens_remaining()
    
    def validate_window_opacity(self, value):
        """Validate opacity is between 0 and 1"""
        if not 0 <= value <= 1:
            raise serializers.ValidationError("Opacity must be between 0 and 1")
        return value
    
    def validate_voice_speed(self, value):
        """Validate voice speed is between 0.5 and 2.0"""
        if not 0.5 <= value <= 2.0:
            raise serializers.ValidationError("Voice speed must be between 0.5 and 2.0")
        return value


class UsageStatisticsSerializer(serializers.Serializer):
    """Serializer for usage statistics endpoint"""
    current_day_tokens = serializers.IntegerField()
    daily_limit = serializers.IntegerField()
    daily_remaining = serializers.IntegerField()
    daily_percentage_used = serializers.FloatField()
    
    current_month_tokens = serializers.IntegerField()
    monthly_limit = serializers.IntegerField()
    monthly_remaining = serializers.IntegerField()
    monthly_percentage_used = serializers.FloatField()
    
    total_tokens_used = serializers.IntegerField()
    is_premium_user = serializers.BooleanField()
    last_reset_date = serializers.DateField()

