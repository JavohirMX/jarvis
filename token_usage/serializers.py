"""
Serializers for TokenUsage API
"""
from rest_framework import serializers
from .models import TokenUsage, UsageQuota


class TokenUsageSerializer(serializers.ModelSerializer):
    """Serializer for TokenUsage model"""
    
    class Meta:
        model = TokenUsage
        fields = (
            'id',
            'date',
            'feature_type',
            'ai_model_used',
            'prompt_tokens',
            'completion_tokens',
            'total_tokens',
            'estimated_cost',
            'request_count',
            'created_at',
        )
        read_only_fields = ('id', 'created_at')


class UsageQuotaSerializer(serializers.ModelSerializer):
    """Serializer for UsageQuota model"""
    remaining = serializers.SerializerMethodField()
    percentage_used = serializers.SerializerMethodField()
    is_exceeded = serializers.SerializerMethodField()
    
    class Meta:
        model = UsageQuota
        fields = (
            'id',
            'quota_type',
            'limit',
            'used',
            'remaining',
            'percentage_used',
            'is_exceeded',
            'reset_date',
            'is_active',
            'created_at',
            'updated_at',
        )
        read_only_fields = ('id', 'created_at', 'updated_at')
    
    def get_remaining(self, obj):
        return obj.remaining()
    
    def get_percentage_used(self, obj):
        return round(obj.percentage_used(), 2)
    
    def get_is_exceeded(self, obj):
        return obj.is_exceeded()


class UsageStatsSerializer(serializers.Serializer):
    """Serializer for aggregated usage statistics"""
    total_tokens = serializers.IntegerField()
    total_requests = serializers.IntegerField()
    total_cost = serializers.DecimalField(max_digits=10, decimal_places=6)
    by_feature = serializers.DictField()
    by_model = serializers.DictField()
    date_range = serializers.DictField()


class QuotaSummarySerializer(serializers.Serializer):
    """Serializer for quota summary"""
    daily = serializers.DictField()
    monthly = serializers.DictField()


class CostBreakdownSerializer(serializers.Serializer):
    """Serializer for cost breakdown"""
    total_cost = serializers.DecimalField(max_digits=10, decimal_places=6)
    by_feature = serializers.DictField()
    by_model = serializers.DictField()
    by_date = serializers.DictField()

