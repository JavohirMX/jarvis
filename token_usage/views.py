"""
API views for token usage and quota management
"""
from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView
from rest_framework.pagination import PageNumberPagination
from django.db.models import Sum, Count
from datetime import date, timedelta
from decimal import Decimal
from drf_spectacular.utils import extend_schema, extend_schema_view
from .models import TokenUsage, UsageQuota
from .serializers import (
    TokenUsageSerializer, UsageQuotaSerializer,
    UsageStatsSerializer, QuotaSummarySerializer,
    CostBreakdownSerializer
)


class TokenUsagePagination(PageNumberPagination):
    """Custom pagination for token usage"""
    page_size = 50
    page_size_query_param = 'page_size'
    max_page_size = 200


@extend_schema(
    summary="Get usage statistics",
    description="Get aggregated token usage statistics with breakdown by feature and model",
    responses={200: UsageStatsSerializer}
)
class UsageStatsView(APIView):
    """
    API endpoint to get aggregated usage statistics
    
    GET /api/usage/stats/ - Get usage statistics
    Query params: 
      - start_date: Filter from date (YYYY-MM-DD)
      - end_date: Filter to date (YYYY-MM-DD)
    """
    permission_classes = (IsAuthenticated,)
    
    def get(self, request):
        """Get usage statistics for the authenticated user"""
        user = request.user
        
        # Get date range from query params
        start_date = request.query_params.get('start_date')
        end_date = request.query_params.get('end_date')
        
        # Build queryset
        queryset = TokenUsage.objects.filter(user=user)
        
        if start_date:
            queryset = queryset.filter(date__gte=start_date)
        if end_date:
            queryset = queryset.filter(date__lte=end_date)
        
        # Aggregate data
        aggregates = queryset.aggregate(
            total_tokens=Sum('total_tokens'),
            total_requests=Sum('request_count'),
            total_cost=Sum('estimated_cost')
        )
        
        # Breakdown by feature
        by_feature = {}
        for feature in queryset.values('feature_type').distinct():
            feature_data = queryset.filter(feature_type=feature['feature_type']).aggregate(
                tokens=Sum('total_tokens'),
                requests=Sum('request_count'),
                cost=Sum('estimated_cost')
            )
            by_feature[feature['feature_type']] = feature_data
        
        # Breakdown by model
        by_model = {}
        for model in queryset.values('ai_model_used').distinct():
            model_data = queryset.filter(ai_model_used=model['ai_model_used']).aggregate(
                tokens=Sum('total_tokens'),
                requests=Sum('request_count'),
                cost=Sum('estimated_cost')
            )
            by_model[model['ai_model_used']] = model_data
        
        data = {
            'total_tokens': aggregates['total_tokens'] or 0,
            'total_requests': aggregates['total_requests'] or 0,
            'total_cost': aggregates['total_cost'] or Decimal('0.0'),
            'by_feature': by_feature,
            'by_model': by_model,
            'date_range': {
                'start': start_date or 'all',
                'end': end_date or 'all'
            }
        }
        
        serializer = UsageStatsSerializer(data)
        return Response(serializer.data, status=status.HTTP_200_OK)


@extend_schema_view(
    get=extend_schema(
        summary="Get usage history",
        description="Get paginated list of token usage records with optional filtering",
        responses={200: TokenUsageSerializer(many=True)}
    )
)
class UsageHistoryView(generics.ListAPIView):
    """
    API endpoint to get usage history
    
    GET /api/usage/history/ - Get paginated usage history
    Query params:
      - date: Filter by date (YYYY-MM-DD)
      - feature_type: Filter by feature type
      - ai_model_used: Filter by AI model
    """
    serializer_class = TokenUsageSerializer
    permission_classes = (IsAuthenticated,)
    pagination_class = TokenUsagePagination
    
    def get_queryset(self):
        """Return usage records for the authenticated user with optional filters"""
        queryset = TokenUsage.objects.filter(user=self.request.user)
        
        # Apply filters
        date_filter = self.request.query_params.get('date')
        if date_filter:
            queryset = queryset.filter(date=date_filter)
        
        feature_filter = self.request.query_params.get('feature_type')
        if feature_filter:
            queryset = queryset.filter(feature_type=feature_filter)
        
        model_filter = self.request.query_params.get('ai_model_used')
        if model_filter:
            queryset = queryset.filter(ai_model_used=model_filter)
        
        return queryset


@extend_schema(
    summary="Get user quotas",
    description="Get current quotas for daily and monthly usage limits",
    responses={200: QuotaSummarySerializer}
)
class UsageQuotasView(APIView):
    """
    API endpoint to get user quotas
    
    GET /api/usage/quotas/ - Get current quotas
    """
    permission_classes = (IsAuthenticated,)
    
    def get(self, request):
        """Get quotas for the authenticated user"""
        user = request.user
        profile = user.profile
        
        # Get daily and monthly usage from profile
        daily_data = {
            'limit': profile.daily_token_limit,
            'used': profile.current_day_tokens,
            'remaining': profile.daily_tokens_remaining(),
            'percentage_used': round((profile.current_day_tokens / profile.daily_token_limit * 100) if profile.daily_token_limit > 0 else 0, 2),
        }
        
        monthly_data = {
            'limit': profile.monthly_token_limit,
            'used': profile.current_month_tokens,
            'remaining': profile.monthly_tokens_remaining(),
            'percentage_used': round((profile.current_month_tokens / profile.monthly_token_limit * 100) if profile.monthly_token_limit > 0 else 0, 2),
        }
        
        data = {
            'daily': daily_data,
            'monthly': monthly_data
        }
        
        serializer = QuotaSummarySerializer(data)
        return Response(serializer.data, status=status.HTTP_200_OK)


@extend_schema(
    summary="Get cost breakdown",
    description="Get detailed cost breakdown by feature, model, and date",
    responses={200: CostBreakdownSerializer}
)
class UsageCostView(APIView):
    """
    API endpoint to get cost breakdown
    
    GET /api/usage/cost/ - Get cost breakdown
    Query params:
      - start_date: Filter from date (YYYY-MM-DD)
      - end_date: Filter to date (YYYY-MM-DD)
    """
    permission_classes = (IsAuthenticated,)
    
    def get(self, request):
        """Get cost breakdown for the authenticated user"""
        user = request.user
        
        # Get date range
        start_date = request.query_params.get('start_date')
        end_date = request.query_params.get('end_date')
        
        queryset = TokenUsage.objects.filter(user=user)
        
        if start_date:
            queryset = queryset.filter(date__gte=start_date)
        if end_date:
            queryset = queryset.filter(date__lte=end_date)
        
        # Total cost
        total_cost = queryset.aggregate(total=Sum('estimated_cost'))['total'] or Decimal('0.0')
        
        # By feature
        by_feature = {}
        for feature in queryset.values('feature_type').distinct():
            cost = queryset.filter(feature_type=feature['feature_type']).aggregate(
                cost=Sum('estimated_cost')
            )['cost'] or Decimal('0.0')
            by_feature[feature['feature_type']] = str(cost)
        
        # By model
        by_model = {}
        for model in queryset.values('ai_model_used').distinct():
            cost = queryset.filter(ai_model_used=model['ai_model_used']).aggregate(
                cost=Sum('estimated_cost')
            )['cost'] or Decimal('0.0')
            by_model[model['ai_model_used']] = str(cost)
        
        # By date (last 7 days if no range specified)
        by_date = {}
        date_queryset = queryset if (start_date or end_date) else queryset.filter(date__gte=date.today() - timedelta(days=7))
        for date_entry in date_queryset.values('date').distinct().order_by('date'):
            cost = date_queryset.filter(date=date_entry['date']).aggregate(
                cost=Sum('estimated_cost')
            )['cost'] or Decimal('0.0')
            by_date[str(date_entry['date'])] = str(cost)
        
        data = {
            'total_cost': total_cost,
            'by_feature': by_feature,
            'by_model': by_model,
            'by_date': by_date
        }
        
        serializer = CostBreakdownSerializer(data)
        return Response(serializer.data, status=status.HTTP_200_OK)
