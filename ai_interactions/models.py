"""
Models for AI interactions, conversations, messages, and memory
"""
from django.db import models
from django.contrib.auth.models import User


class Conversation(models.Model):
    """Model to store conversations with AI"""
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='conversations')
    title = models.CharField(max_length=255)
    total_tokens_used = models.IntegerField(default=0)
    message_count = models.IntegerField(default=0)
    is_active = models.BooleanField(default=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = 'Conversation'
        verbose_name_plural = 'Conversations'
        ordering = ['-updated_at']
    
    def __str__(self):
        return f"{self.user.username} - {self.title}"
    
    def update_stats(self):
        """Update conversation statistics"""
        messages = self.messages.all()
        self.message_count = messages.count()
        self.total_tokens_used = sum(msg.total_tokens for msg in messages)
        self.save(update_fields=['message_count', 'total_tokens_used'])


class AIMessage(models.Model):
    """Model to store individual AI messages"""
    
    ROLE_CHOICES = [
        ('user', 'User'),
        ('assistant', 'Assistant'),
        ('system', 'System'),
    ]
    
    conversation = models.ForeignKey(Conversation, on_delete=models.CASCADE, related_name='messages')
    role = models.CharField(max_length=20, choices=ROLE_CHOICES)
    content = models.TextField()
    context_data = models.JSONField(default=dict, blank=True)
    ai_model_used = models.CharField(max_length=100)
    
    # Token tracking
    prompt_tokens = models.IntegerField(default=0)
    completion_tokens = models.IntegerField(default=0)
    total_tokens = models.IntegerField(default=0)
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = 'AI Message'
        verbose_name_plural = 'AI Messages'
        ordering = ['created_at']
    
    def __str__(self):
        return f"{self.role} - {self.content[:50]}"
    
    def save(self, *args, **kwargs):
        """Calculate total tokens if not set"""
        if not self.total_tokens:
            self.total_tokens = self.prompt_tokens + self.completion_tokens
        super().save(*args, **kwargs)


class AIMemory(models.Model):
    """Model to store AI memory/context for users"""
    
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='ai_memory')
    key_facts = models.JSONField(default=dict)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = 'AI Memory'
        verbose_name_plural = 'AI Memories'
    
    def __str__(self):
        return f"AI Memory for {self.user.username}"
