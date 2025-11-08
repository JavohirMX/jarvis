"""
Admin interface for UserProfile
"""
from django.contrib import admin
from .models import UserProfile


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    """Admin interface for UserProfile model"""
    
    list_display = (
        'user',
        'theme',
        'ai_response_length',
        'is_premium_user',
        'current_day_tokens',
        'current_month_tokens',
        'total_tokens_used',
        'created_at',
    )
    
    list_filter = (
        'theme',
        'ai_response_length',
        'is_premium_user',
        'voice_enabled',
        'notifications_enabled',
        'created_at',
    )
    
    search_fields = (
        'user__username',
        'user__email',
        'user__first_name',
        'user__last_name',
    )
    
    readonly_fields = (
        'created_at',
        'updated_at',
        'last_reset_date',
    )
    
    fieldsets = (
        ('User', {
            'fields': ('user',)
        }),
        ('Theme Preferences', {
            'fields': ('theme', 'theme_custom_colors')
        }),
        ('AI Settings', {
            'fields': ('ai_response_length',)
        }),
        ('Notification Settings', {
            'fields': ('notifications_enabled', 'notification_sound', 'notification_position')
        }),
        ('Window Preferences', {
            'fields': (
                'window_default_x',
                'window_default_y',
                'window_default_width',
                'window_default_height',
                'window_opacity',
            ),
            'classes': ('collapse',)
        }),
        ('Voice Settings', {
            'fields': ('voice_enabled', 'preferred_voice', 'voice_speed', 'voice_language')
        }),
        ('Token Usage', {
            'fields': (
                'total_tokens_used',
                'current_month_tokens',
                'current_day_tokens',
                'daily_token_limit',
                'monthly_token_limit',
                'is_premium_user',
                'last_reset_date',
            )
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    actions = ['reset_daily_tokens', 'reset_monthly_tokens', 'upgrade_to_premium']
    
    def reset_daily_tokens(self, request, queryset):
        """Admin action to reset daily tokens for selected profiles"""
        count = 0
        for profile in queryset:
            profile.reset_daily_tokens()
            count += 1
        self.message_user(request, f"Reset daily tokens for {count} profile(s)")
    reset_daily_tokens.short_description = "Reset daily token count"
    
    def reset_monthly_tokens(self, request, queryset):
        """Admin action to reset monthly tokens for selected profiles"""
        count = 0
        for profile in queryset:
            profile.reset_monthly_tokens()
            count += 1
        self.message_user(request, f"Reset monthly tokens for {count} profile(s)")
    reset_monthly_tokens.short_description = "Reset monthly token count"
    
    def upgrade_to_premium(self, request, queryset):
        """Admin action to upgrade users to premium"""
        from django.conf import settings
        count = queryset.update(
            is_premium_user=True,
            daily_token_limit=settings.PREMIUM_DAILY_TOKEN_LIMIT,
            monthly_token_limit=settings.PREMIUM_MONTHLY_TOKEN_LIMIT,
        )
        self.message_user(request, f"Upgraded {count} profile(s) to premium")
    upgrade_to_premium.short_description = "Upgrade to premium"
