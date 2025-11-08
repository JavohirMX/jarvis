"""
API views for voice commands
"""
from rest_framework import generics
from rest_framework.permissions import IsAuthenticated
from rest_framework.pagination import PageNumberPagination
from drf_spectacular.utils import extend_schema_view, extend_schema
from .models import VoiceCommand
from .serializers import VoiceCommandSerializer


class VoiceCommandPagination(PageNumberPagination):
    """Pagination for voice commands"""
    page_size = 20
    page_size_query_param = 'page_size'
    max_page_size = 100


@extend_schema_view(
    get=extend_schema(
        summary="Get voice command history",
        description="Get paginated list of voice commands",
        responses={200: VoiceCommandSerializer(many=True)}
    )
)
class VoiceHistoryView(generics.ListAPIView):
    """
    API endpoint to get voice command history
    
    GET /api/voice/history/ - Get voice command history
    """
    serializer_class = VoiceCommandSerializer
    permission_classes = (IsAuthenticated,)
    pagination_class = VoiceCommandPagination
    
    def get_queryset(self):
        return VoiceCommand.objects.filter(user=self.request.user)
