"""
API views for UserProfile management
"""
from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView
from drf_spectacular.utils import extend_schema, extend_schema_view, OpenApiExample
from django.conf import settings
from .serializers import UserProfileSerializer, UsageStatisticsSerializer


@extend_schema_view(
    get=extend_schema(
        summary="Get user profile",
        description="Retrieve the authenticated user's profile with all settings and usage statistics",
        responses={200: UserProfileSerializer}
    ),
    put=extend_schema(
        summary="Update user profile (full)",
        description="Update all profile settings (requires all fields)",
        request=UserProfileSerializer,
        responses={200: UserProfileSerializer}
    ),
    patch=extend_schema(
        summary="Update user profile (partial)",
        description="Update specific profile settings (partial update)",
        request=UserProfileSerializer,
        responses={200: UserProfileSerializer}
    ),
)
class ProfileDetailView(generics.RetrieveUpdateAPIView):
    """
    API endpoint to get and update current user's profile
    
    GET /api/profile/ - Get current user's profile
    PUT /api/profile/ - Update profile (full update)
    PATCH /api/profile/ - Update profile (partial update)
    """
    serializer_class = UserProfileSerializer
    permission_classes = (IsAuthenticated,)
    
    def get_object(self):
        """Return the profile for the currently authenticated user"""
        return self.request.user.profile
    
    def update(self, request, *args, **kwargs):
        """Override update to handle avatar uploads"""
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        
        # If using MinIO, ensure bucket exists before saving
        if 'avatar' in request.FILES and getattr(settings, 'USE_MINIO', False):
            try:
                from config.minio_service import get_minio_service
                minio_service = get_minio_service()
                bucket_name = getattr(settings, 'MINIO_BUCKET_NAME', 'jarvis-media')
                minio_service.ensure_bucket_exists(bucket_name)
            except Exception as e:
                import logging
                logger = logging.getLogger(__name__)
                logger.warning(f"Could not ensure MinIO bucket exists: {e}")
                # Continue anyway - storage might still work
        
        self.perform_update(serializer)
        
        if getattr(instance, '_prefetched_objects_cache', None):
            instance._prefetched_objects_cache = {}
        
        return Response(serializer.data)


@extend_schema(
    summary="Reset profile settings",
    description="Reset all profile settings to default values. Token usage is not affected.",
    request=None,
    responses={
        200: UserProfileSerializer,
    },
    examples=[
        OpenApiExample(
            'Success Response',
            value={
                'message': 'Profile settings reset to defaults',
                'profile': {
                    'theme': 'dark',
                    'ai_response_length': 'medium',
                    # ... other default values
                }
            },
            response_only=True,
        ),
    ],
)
class ProfileResetView(APIView):
    """
    API endpoint to reset profile settings to defaults
    
    POST /api/profile/reset/ - Reset all settings to default values
    """
    permission_classes = (IsAuthenticated,)
    
    def post(self, request):
        """Reset profile settings to defaults"""
        profile = request.user.profile
        profile.reset_to_defaults()
        
        serializer = UserProfileSerializer(profile)
        return Response({
            'message': 'Profile settings reset to defaults',
            'profile': serializer.data
        }, status=status.HTTP_200_OK)


@extend_schema(
    summary="Get usage statistics",
    description="Get detailed token usage statistics including daily, monthly, and lifetime usage",
    responses={200: UsageStatisticsSerializer},
    examples=[
        OpenApiExample(
            'Usage Statistics Response',
            value={
                'current_day_tokens': 500,
                'daily_limit': 10000,
                'daily_remaining': 9500,
                'daily_percentage_used': 5.0,
                'current_month_tokens': 15000,
                'monthly_limit': 100000,
                'monthly_remaining': 85000,
                'monthly_percentage_used': 15.0,
                'total_tokens_used': 125000,
                'is_premium_user': False,
                'last_reset_date': '2024-01-15'
            },
            response_only=True,
        ),
    ],
)
class ProfileUsageView(APIView):
    """
    API endpoint to get detailed usage statistics
    
    GET /api/profile/usage/ - Get token usage statistics
    """
    permission_classes = (IsAuthenticated,)
    
    def get(self, request):
        """Get usage statistics for the authenticated user"""
        profile = request.user.profile
        
        # Calculate percentages
        daily_percentage = (profile.current_day_tokens / profile.daily_token_limit * 100) if profile.daily_token_limit > 0 else 0
        monthly_percentage = (profile.current_month_tokens / profile.monthly_token_limit * 100) if profile.monthly_token_limit > 0 else 0
        
        data = {
            'current_day_tokens': profile.current_day_tokens,
            'daily_limit': profile.daily_token_limit,
            'daily_remaining': profile.daily_tokens_remaining(),
            'daily_percentage_used': round(daily_percentage, 2),
            
            'current_month_tokens': profile.current_month_tokens,
            'monthly_limit': profile.monthly_token_limit,
            'monthly_remaining': profile.monthly_tokens_remaining(),
            'monthly_percentage_used': round(monthly_percentage, 2),
            
            'total_tokens_used': profile.total_tokens_used,
            'is_premium_user': profile.is_premium_user,
            'last_reset_date': profile.last_reset_date,
        }
        
        serializer = UsageStatisticsSerializer(data)
        return Response(serializer.data, status=status.HTTP_200_OK)
