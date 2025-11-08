"""
Models for token usage tracking and quota management
"""
from django.db import models
from django.contrib.auth.models import User
from decimal import Decimal


class TokenUsage(models.Model):
    """
    Model to track detailed token usage per user, feature, and model
    """
    
    FEATURE_CHOICES = [
        ('chat', 'Chat'),
        ('summarize', 'Summarize'),
        ('translate', 'Translate'),
        ('explain_code', 'Explain Code'),
        ('voice_transcribe', 'Voice Transcription'),
        ('voice_tts', 'Text-to-Speech'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='token_usage')
    date = models.DateField(db_index=True)
    feature_type = models.CharField(max_length=50, choices=FEATURE_CHOICES, db_index=True)
    ai_model_used = models.CharField(max_length=100)
    
    # Token counts
    prompt_tokens = models.IntegerField(default=0)
    completion_tokens = models.IntegerField(default=0)
    total_tokens = models.IntegerField(default=0)
    
    # Cost and request tracking
    estimated_cost = models.DecimalField(max_digits=10, decimal_places=6, default=Decimal('0.0'))
    request_count = models.IntegerField(default=1)
    
    # Timestamp
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = 'Token Usage'
        verbose_name_plural = 'Token Usage Records'
        ordering = ['-date', '-created_at']
        indexes = [
            models.Index(fields=['user', 'date']),
            models.Index(fields=['user', 'feature_type']),
            models.Index(fields=['date', 'feature_type']),
        ]
    
    def __str__(self):
        return f"{self.user.username} - {self.date} - {self.feature_type} - {self.total_tokens} tokens"
    
    def save(self, *args, **kwargs):
        """Calculate total tokens if not set"""
        if not self.total_tokens:
            self.total_tokens = self.prompt_tokens + self.completion_tokens
        super().save(*args, **kwargs)


class UsageQuota(models.Model):
    """
    Model to track and manage user quotas
    """
    
    QUOTA_TYPE_CHOICES = [
        ('daily', 'Daily'),
        ('monthly', 'Monthly'),
        ('lifetime', 'Lifetime'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='quotas')
    quota_type = models.CharField(max_length=20, choices=QUOTA_TYPE_CHOICES, db_index=True)
    limit = models.IntegerField()
    used = models.IntegerField(default=0)
    reset_date = models.DateTimeField()
    is_active = models.BooleanField(default=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = 'Usage Quota'
        verbose_name_plural = 'Usage Quotas'
        ordering = ['-created_at']
        unique_together = ['user', 'quota_type']
    
    def __str__(self):
        return f"{self.user.username} - {self.quota_type} quota: {self.used}/{self.limit}"
    
    def remaining(self):
        """Calculate remaining quota"""
        return max(0, self.limit - self.used)
    
    def percentage_used(self):
        """Calculate percentage of quota used"""
        if self.limit == 0:
            return 0
        return (self.used / self.limit) * 100
    
    def is_exceeded(self):
        """Check if quota is exceeded"""
        return self.used >= self.limit
    
    def reset(self, new_limit=None):
        """Reset quota usage"""
        self.used = 0
        if new_limit is not None:
            self.limit = new_limit
        self.save()
