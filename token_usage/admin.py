"""
Admin interface for token usage and quotas
"""
from django.contrib import admin
from django.db.models import Sum
from .models import TokenUsage, UsageQuota


@admin.register(TokenUsage)
class TokenUsageAdmin(admin.ModelAdmin):
    """Admin interface for TokenUsage model"""
    
    list_display = (
        'user',
        'date',
        'feature_type',
        'ai_model_used',
        'total_tokens',
        'estimated_cost',
        'request_count',
        'created_at',
    )
    
    list_filter = (
        'date',
        'feature_type',
        'ai_model_used',
        'created_at',
    )
    
    search_fields = (
        'user__username',
        'user__email',
        'feature_type',
        'ai_model_used',
    )
    
    readonly_fields = ('created_at',)
    
    date_hierarchy = 'date'
    
    fieldsets = (
        ('User', {
            'fields': ('user',)
        }),
        ('Usage Details', {
            'fields': ('date', 'feature_type', 'ai_model_used')
        }),
        ('Token Counts', {
            'fields': ('prompt_tokens', 'completion_tokens', 'total_tokens')
        }),
        ('Cost & Requests', {
            'fields': ('estimated_cost', 'request_count')
        }),
        ('Timestamp', {
            'fields': ('created_at',)
        }),
    )
    
    def get_queryset(self, request):
        """Optimize queryset with select_related"""
        qs = super().get_queryset(request)
        return qs.select_related('user')


@admin.register(UsageQuota)
class UsageQuotaAdmin(admin.ModelAdmin):
    """Admin interface for UsageQuota model"""
    
    list_display = (
        'user',
        'quota_type',
        'used',
        'limit',
        'percentage_display',
        'is_active',
        'reset_date',
    )
    
    list_filter = (
        'quota_type',
        'is_active',
        'reset_date',
    )
    
    search_fields = (
        'user__username',
        'user__email',
    )
    
    readonly_fields = ('created_at', 'updated_at', 'percentage_display')
    
    fieldsets = (
        ('User', {
            'fields': ('user',)
        }),
        ('Quota Settings', {
            'fields': ('quota_type', 'limit', 'used', 'percentage_display')
        }),
        ('Status', {
            'fields': ('is_active', 'reset_date')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    actions = ['reset_quotas', 'deactivate_quotas']
    
    def percentage_display(self, obj):
        """Display percentage used"""
        return f"{obj.percentage_used():.1f}%"
    percentage_display.short_description = "Usage %"
    
    def reset_quotas(self, request, queryset):
        """Admin action to reset selected quotas"""
        count = 0
        for quota in queryset:
            quota.reset()
            count += 1
        self.message_user(request, f"Reset {count} quota(s)")
    reset_quotas.short_description = "Reset selected quotas"
    
    def deactivate_quotas(self, request, queryset):
        """Admin action to deactivate selected quotas"""
        count = queryset.update(is_active=False)
        self.message_user(request, f"Deactivated {count} quota(s)")
    deactivate_quotas.short_description = "Deactivate selected quotas"
