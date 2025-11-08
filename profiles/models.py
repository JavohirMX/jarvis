"""
UserProfile model for storing user preferences, settings, and token usage tracking
"""
from django.db import models
from django.contrib.auth.models import User
from django.conf import settings
from datetime import datetime


class UserProfile(models.Model):
    """Extended user profile with preferences, settings, and token tracking"""
    
    THEME_CHOICES = [
        ('dark', 'Dark'),
        ('light', 'Light'),
        ('custom', 'Custom'),
    ]
    
    AI_RESPONSE_LENGTH_CHOICES = [
        ('short', 'Short'),
        ('medium', 'Medium'),
        ('long', 'Long'),
    ]
    
    NOTIFICATION_POSITION_CHOICES = [
        ('top-left', 'Top Left'),
        ('top-right', 'Top Right'),
        ('bottom-left', 'Bottom Left'),
        ('bottom-right', 'Bottom Right'),
    ]
    
    VOICE_CHOICES = [
        ('alloy', 'Alloy'),
        ('echo', 'Echo'),
        ('fable', 'Fable'),
        ('onyx', 'Onyx'),
        ('nova', 'Nova'),
        ('shimmer', 'Shimmer'),
    ]
    
    # User relationship
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    
    # Profile information
    # Note: ImageField automatically uses STORAGES['default'] which is MinIO when USE_MINIO=True
    avatar = models.ImageField(upload_to='avatars/', null=True, blank=True)
    
    # Theme preferences
    theme = models.CharField(max_length=20, choices=THEME_CHOICES, default='dark')
    theme_custom_colors = models.JSONField(default=dict, blank=True)
    
    # AI settings
    ai_response_length = models.CharField(
        max_length=20,
        choices=AI_RESPONSE_LENGTH_CHOICES,
        default='medium'
    )
    
    # Notification settings
    notifications_enabled = models.BooleanField(default=True)
    notification_sound = models.BooleanField(default=True)
    notification_position = models.CharField(
        max_length=20,
        choices=NOTIFICATION_POSITION_CHOICES,
        default='bottom-right'
    )
    
    # Window preferences
    window_default_x = models.IntegerField(default=100)
    window_default_y = models.IntegerField(default=100)
    window_default_width = models.IntegerField(default=400)
    window_default_height = models.IntegerField(default=600)
    window_opacity = models.FloatField(default=0.95)
    
    # Voice settings
    voice_enabled = models.BooleanField(default=True)
    preferred_voice = models.CharField(max_length=20, choices=VOICE_CHOICES, default='alloy')
    voice_speed = models.FloatField(default=1.0)
    voice_language = models.CharField(max_length=10, default='en-US')
    
    # Token usage tracking
    total_tokens_used = models.BigIntegerField(default=0)
    current_month_tokens = models.IntegerField(default=0)
    current_day_tokens = models.IntegerField(default=0)
    daily_token_limit = models.IntegerField(default=settings.DEFAULT_DAILY_TOKEN_LIMIT)
    monthly_token_limit = models.IntegerField(default=settings.DEFAULT_MONTHLY_TOKEN_LIMIT)
    last_reset_date = models.DateField(auto_now_add=True)
    is_premium_user = models.BooleanField(default=False)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = 'User Profile'
        verbose_name_plural = 'User Profiles'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"Profile of {self.user.username}"
    
    def reset_to_defaults(self):
        """Reset profile settings to default values"""
        self.theme = 'dark'
        self.theme_custom_colors = {}
        self.ai_response_length = 'medium'
        self.notifications_enabled = True
        self.notification_sound = True
        self.notification_position = 'bottom-right'
        self.window_default_x = 100
        self.window_default_y = 100
        self.window_default_width = 400
        self.window_default_height = 600
        self.window_opacity = 0.95
        self.voice_enabled = True
        self.preferred_voice = 'alloy'
        self.voice_speed = 1.0
        self.voice_language = 'en-US'
        self.save()
    
    def increment_token_usage(self, tokens):
        """Increment token usage counters"""
        self.total_tokens_used += tokens
        self.current_month_tokens += tokens
        self.current_day_tokens += tokens
        self.save(update_fields=['total_tokens_used', 'current_month_tokens', 'current_day_tokens'])
    
    def reset_daily_tokens(self):
        """Reset daily token counter"""
        self.current_day_tokens = 0
        self.last_reset_date = datetime.now().date()
        self.save(update_fields=['current_day_tokens', 'last_reset_date'])
    
    def reset_monthly_tokens(self):
        """Reset monthly token counter"""
        self.current_month_tokens = 0
        self.last_reset_date = datetime.now().date()
        self.save(update_fields=['current_month_tokens', 'last_reset_date'])
    
    def has_daily_quota_remaining(self):
        """Check if user has daily quota remaining"""
        return self.current_day_tokens < self.daily_token_limit
    
    def has_monthly_quota_remaining(self):
        """Check if user has monthly quota remaining"""
        return self.current_month_tokens < self.monthly_token_limit
    
    def daily_tokens_remaining(self):
        """Get remaining daily tokens"""
        return max(0, self.daily_token_limit - self.current_day_tokens)
    
    def monthly_tokens_remaining(self):
        """Get remaining monthly tokens"""
        return max(0, self.monthly_token_limit - self.current_month_tokens)
