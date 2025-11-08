"""
API views for AI interactions
"""
from rest_framework import generics, status, serializers
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.pagination import PageNumberPagination
from rest_framework.views import APIView
from drf_spectacular.utils import extend_schema, extend_schema_view, inline_serializer
from datetime import date
from decimal import Decimal
from .models import Conversation, AIMessage, AIMemory
from .serializers import (
    ConversationSerializer, ConversationListSerializer,
    AIMemorySerializer
)


class ConversationPagination(PageNumberPagination):
    """Pagination for conversations"""
    page_size = 20
    page_size_query_param = 'page_size'
    max_page_size = 100


@extend_schema_view(
    get=extend_schema(
        summary="List conversations",
        description="Get list of user's conversations",
        responses={200: ConversationListSerializer(many=True)}
    )
)
class ConversationListView(generics.ListAPIView):
    """
    API endpoint to list user's conversations
    
    GET /api/ai/conversations/ - List conversations
    """
    serializer_class = ConversationListSerializer
    permission_classes = (IsAuthenticated,)
    pagination_class = ConversationPagination
    
    def get_queryset(self):
        return Conversation.objects.filter(user=self.request.user)


@extend_schema_view(
    get=extend_schema(
        summary="Get conversation",
        description="Get conversation with all messages",
        responses={200: ConversationSerializer}
    ),
    delete=extend_schema(
        summary="Delete conversation",
        description="Delete a conversation and all its messages",
        responses={204: None}
    )
)
class ConversationDetailView(generics.RetrieveDestroyAPIView):
    """
    API endpoint to get or delete a conversation
    
    GET /api/ai/conversations/{id}/ - Get conversation with messages
    DELETE /api/ai/conversations/{id}/ - Delete conversation
    """
    serializer_class = ConversationSerializer
    permission_classes = (IsAuthenticated,)
    
    def get_queryset(self):
        return Conversation.objects.filter(user=self.request.user)


@extend_schema(
    summary="Get AI memory",
    description="Get user's AI memory containing key facts and preferences",
    responses={200: AIMemorySerializer}
)
class AIMemoryView(generics.RetrieveAPIView):
    """
    API endpoint to get user's AI memory
    
    GET /api/ai/memory/ - Get AI memory
    """
    serializer_class = AIMemorySerializer
    permission_classes = (IsAuthenticated,)
    
    def get_object(self):
        memory, created = AIMemory.objects.get_or_create(user=self.request.user)
        return memory


@extend_schema(
    request={
        'multipart/form-data': {
            'type': 'object',
            'properties': {
                'message': {
                    'type': 'string',
                    'description': 'The message text to send to AI'
                },
                'conversation_id': {
                    'type': 'integer',
                    'description': 'Optional conversation ID. Creates new conversation if not provided',
                    'nullable': True
                },
                'context': {
                    'type': 'object',
                    'description': 'Optional context data (clipboard, active_app, etc.)',
                    'nullable': True
                },
                'provider': {
                    'type': 'string',
                    'description': 'Optional AI provider selection (openai, anthropic, gemini)',
                    'nullable': True
                },
                'image': {
                    'type': 'string',
                    'format': 'binary',
                    'description': 'Optional image file (PNG, JPEG, WEBP, HEIC, HEIF). Max size: 50MB',
                    'nullable': True
                }
            },
            'required': ['message']
        }
    },
    responses={
        200: inline_serializer(
            name='ChatResponse',
            fields={
                'response': serializers.CharField(),
                'conversation_id': serializers.IntegerField(),
                'message_id': serializers.IntegerField(),
                'tokens': serializers.JSONField(),
                'usage_stats': serializers.JSONField(),
            }
        )
    },
    summary="Send message to AI (with optional image)",
    description="""
    Send a message to AI and get a response. Supports multimodal requests with images.
    
    **Image Support (Gemini only for now):**
    - Supported formats: PNG, JPEG, WEBP, HEIC, HEIF
    - Maximum file size: 50MB
    - Images are stored in MinIO and included in conversation history
    - Token cost includes image processing (based on image dimensions)
    
    **Request Format:**
    Use `multipart/form-data` when including an image, otherwise standard JSON.
    
    Creates a new conversation if conversation_id is not provided.
    """
)
class AIChatView(APIView):
    """
    **Main AI Chat Endpoint** - Send messages to AI
    
    POST /api/ai/chat/ - Send message and get AI response
    
    Request body:
    {
        "message": "Your message here",
        "conversation_id": 123,  # Optional, creates new if not provided
        "context": {             # Optional context
            "clipboard": "...",
            "active_app": "..."
        }
    }
    """
    permission_classes = (IsAuthenticated,)
    
    def post(self, request):
        user = request.user
        message_text = request.data.get('message', '').strip()
        conversation_id = request.data.get('conversation_id')
        context = request.data.get('context', {})
        
        # Handle image upload (optional)
        image_file = request.FILES.get('image')
        image_data = None
        image_mime_type = None
        image_size = None
        saved_image = None
        
        if image_file:
            # Validate MIME type
            allowed_mime_types = [
                'image/png', 'image/jpeg', 'image/jpg',
                'image/webp', 'image/heic', 'image/heif'
            ]
            
            # Get MIME type from file
            content_type = image_file.content_type
            if content_type not in allowed_mime_types:
                return Response(
                    {'error': f'Invalid image format. Allowed formats: PNG, JPEG, WEBP, HEIC, HEIF'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Check file size (Gemini supports up to 20MB for inline, larger for File API)
            # We'll set a reasonable limit of 50MB
            max_size = 50 * 1024 * 1024  # 50MB
            if image_file.size > max_size:
                return Response(
                    {'error': f'Image too large. Maximum size: 50MB'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Read image data for processing
            image_data = image_file.read()
            image_mime_type = content_type
            image_size = image_file.size
            
            # Reset file pointer for saving
            image_file.seek(0)
        
        if not message_text:
            return Response(
                {'error': 'Message is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Check quota
        profile = user.profile
        if not profile.has_daily_quota_remaining():
            return Response(
                {'error': 'Daily quota exceeded'},
                status=status.HTTP_429_TOO_MANY_REQUESTS
            )
        
        # Get or create conversation
        if conversation_id:
            try:
                conversation = Conversation.objects.get(id=conversation_id, user=user)
            except Conversation.DoesNotExist:
                return Response(
                    {'error': 'Conversation not found'},
                    status=status.HTTP_404_NOT_FOUND
                )
        else:
            # Create new conversation with first message as title
            title = message_text[:50] + ('...' if len(message_text) > 50 else '')
            conversation = Conversation.objects.create(user=user, title=title)
        
        # Save user message to database (with optional image)
        user_message = AIMessage(
            conversation=conversation,
            role='user',
            content=message_text,
            context_data=context,
            ai_model_used='gpt-4',  # Will be from settings
            prompt_tokens=0,
            completion_tokens=0,
            total_tokens=0
        )
        
        # Save image if provided
        if image_file:
            user_message.image = image_file
            user_message.image_mime_type = image_mime_type
            user_message.image_size = image_size
        
        user_message.save()
        
        # Get image URL after saving (MinIO will generate the URL)
        if image_file and user_message.image:
            user_message.image_url = user_message.image.url
            user_message.save(update_fields=['image_url'])
        
        # Get conversation history for context
        conversation_history = []
        if conversation_id:
            # Get last messages for context
            recent_messages = conversation.messages.order_by('created_at')[:20]
            conversation_history = [
                {'role': msg.role, 'content': msg.content}
                for msg in recent_messages
            ]
        
        # Call AI API (supports OpenAI, Anthropic, Gemini)
        try:
            ai_response_text, prompt_tokens, completion_tokens, total_tokens = self._get_ai_response(
                message_text, context, user, conversation_history,
                image_data, image_mime_type
            )
        except Exception as e:
            return Response(
                {'error': f'AI processing failed: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
        
        # Save AI response
        ai_message = AIMessage.objects.create(
            conversation=conversation,
            role='assistant',
            content=ai_response_text,
            ai_model_used='gpt-4',
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
            total_tokens=total_tokens
        )
        
        # Update conversation stats
        conversation.update_stats()
        
        # Update user token usage
        profile.increment_token_usage(total_tokens)
        
        # Track usage in token_usage app
        from token_usage.models import TokenUsage
        TokenUsage.objects.create(
            user=user,
            date=date.today(),
            feature_type='chat',
            ai_model_used='gpt-4',
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
            total_tokens=total_tokens,
            estimated_cost=Decimal('0.001') * total_tokens,  # Example pricing
            request_count=1
        )
        
        # Prepare response
        profile.refresh_from_db()
        return Response({
            'response': ai_response_text,
            'conversation_id': conversation.id,
            'message_id': ai_message.id,
            'tokens': {
                'prompt': prompt_tokens,
                'completion': completion_tokens,
                'total': total_tokens
            },
            'usage_stats': {
                'daily_used': profile.current_day_tokens,
                'daily_limit': profile.daily_token_limit,
                'daily_remaining': profile.daily_tokens_remaining(),
                'monthly_used': profile.current_month_tokens,
                'monthly_limit': profile.monthly_token_limit,
            }
        })
    
    def _get_ai_response(
        self, 
        message: str, 
        context: dict, 
        user, 
        conversation_history: list = None,
        image_data: bytes = None,
        image_mime_type: str = None
    ) -> tuple:
        """
        Get AI response using the service layer
        Supports multiple providers (OpenAI, Anthropic, Gemini)
        
        Returns:
            Tuple of (response_text, prompt_tokens, completion_tokens, total_tokens)
        """
        from .services import AIService
        
        # Get provider preference from request or use default
        provider = self.request.data.get('provider')  # Optional: allow per-request provider selection
        
        try:
            # Initialize AI service
            ai_service = AIService(user=user, provider=provider)
            
            # Get AI response (with optional image)
            response = ai_service.chat(
                message=message,
                context=context,
                conversation_history=conversation_history,
                temperature=0.7,
                max_tokens=None,  # Use provider default
                image_data=image_data,
                image_mime_type=image_mime_type
            )
            
            return (
                response.content,
                response.prompt_tokens,
                response.completion_tokens,
                response.total_tokens
            )
            
        except Exception as e:
            # Log error and return helpful message
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"AI API error for user {user.id}: {str(e)}")
            
            # Return error message to user
            raise Exception(f"AI service error: {str(e)}")


@extend_schema(
    request=inline_serializer(
        name='SummarizeRequest',
        fields={
            'text': serializers.CharField(),
            'length': serializers.ChoiceField(choices=['short', 'medium', 'long'], default='medium'),
        }
    ),
    responses={
        200: inline_serializer(
            name='SummarizeResponse',
            fields={
                'summary': serializers.CharField(),
                'tokens': serializers.JSONField(),
                'usage_stats': serializers.JSONField(),
            }
        )
    },
    summary="Summarize text",
    description="Summarize provided text using AI"
)
class AISummarizeView(APIView):
    """
    POST /api/ai/summarize/ - Summarize text
    """
    permission_classes = (IsAuthenticated,)
    
    def post(self, request):
        text = request.data.get('text', '').strip()
        length = request.data.get('length', 'medium')
        
        if not text:
            return Response({'error': 'Text is required'}, status=status.HTTP_400_BAD_REQUEST)
        
        # Check quota
        if not request.user.profile.has_daily_quota_remaining():
            return Response({'error': 'Daily quota exceeded'}, status=status.HTTP_429_TOO_MANY_REQUESTS)
        
        # Use AI service for summarization
        from .services import AIService
        
        try:
            ai_service = AIService(user=request.user)
            response = ai_service.summarize(text, length)
            
            summary = response.content
            tokens = response.total_tokens
            
            # Track usage
            request.user.profile.increment_token_usage(tokens)
        except Exception as e:
            return Response(
                {'error': f'Summarization failed: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
        
        from token_usage.models import TokenUsage
        TokenUsage.objects.create(
            user=request.user,
            date=date.today(),
            feature_type='summarize',
            ai_model_used='gpt-4',
            total_tokens=tokens,
            estimated_cost=Decimal('0.001') * tokens,
            request_count=1
        )
        
        profile = request.user.profile
        return Response({
            'summary': summary,
            'tokens': {'total': tokens},
            'usage_stats': {
                'daily_used': profile.current_day_tokens,
                'daily_remaining': profile.daily_tokens_remaining(),
            }
        })


@extend_schema(
    request=inline_serializer(
        name='TranslateRequest',
        fields={
            'text': serializers.CharField(),
            'target_language': serializers.CharField(),
        }
    ),
    responses={
        200: inline_serializer(
            name='TranslateResponse',
            fields={
                'translation': serializers.CharField(),
                'tokens': serializers.JSONField(),
                'model': serializers.CharField(),
                'provider': serializers.CharField(),
            }
        )
    },
    summary="Translate text",
    description="Translate text to target language"
)
class AITranslateView(APIView):
    """
    POST /api/ai/translate/ - Translate text
    """
    permission_classes = (IsAuthenticated,)
    
    def post(self, request):
        text = request.data.get('text', '').strip()
        target_language = request.data.get('target_language', 'en')
        
        if not text:
            return Response({'error': 'Text is required'}, status=status.HTTP_400_BAD_REQUEST)
        
        # Use AI service for translation
        from .services import AIService
        
        try:
            ai_service = AIService(user=request.user)
            response = ai_service.translate(text, target_language)
            
            translation = response.content
            tokens = response.total_tokens
            
            # Track usage
            request.user.profile.increment_token_usage(tokens)
            
            from token_usage.models import TokenUsage
            TokenUsage.objects.create(
                user=request.user,
                date=date.today(),
                feature_type='translate',
                ai_model_used=response.model,
                total_tokens=tokens,
                estimated_cost=Decimal(str(response.estimated_cost)),
                request_count=1
            )
            
            return Response({
                'translation': translation,
                'tokens': {'total': tokens},
                'model': response.model,
                'provider': response.provider
            })
        except Exception as e:
            return Response(
                {'error': f'Translation failed: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


@extend_schema(
    request=inline_serializer(
        name='ExplainCodeRequest',
        fields={
            'code': serializers.CharField(),
            'language': serializers.CharField(required=False),
        }
    ),
    responses={
        200: inline_serializer(
            name='ExplainCodeResponse',
            fields={
                'explanation': serializers.CharField(),
                'tokens': serializers.JSONField(),
                'model': serializers.CharField(),
                'provider': serializers.CharField(),
            }
        )
    },
    summary="Explain code",
    description="Get AI explanation of code snippet"
)
class AIExplainCodeView(APIView):
    """
    POST /api/ai/explain-code/ - Explain code
    """
    permission_classes = (IsAuthenticated,)
    
    def post(self, request):
        code = request.data.get('code', '').strip()
        language = request.data.get('language', 'auto-detect')
        
        if not code:
            return Response({'error': 'Code is required'}, status=status.HTTP_400_BAD_REQUEST)
        
        # Use AI service for code explanation
        from .services import AIService
        
        try:
            ai_service = AIService(user=request.user)
            response = ai_service.explain_code(code, language)
            
            explanation = response.content
            tokens = response.total_tokens
            
            # Track usage
            request.user.profile.increment_token_usage(tokens)
            
            from token_usage.models import TokenUsage
            TokenUsage.objects.create(
                user=request.user,
                date=date.today(),
                feature_type='explain_code',
                ai_model_used=response.model,
                total_tokens=tokens,
                estimated_cost=Decimal(str(response.estimated_cost)),
                request_count=1
            )
            
            return Response({
                'explanation': explanation,
                'tokens': {'total': tokens},
                'model': response.model,
                'provider': response.provider
            })
        except Exception as e:
            return Response(
                {'error': f'Code explanation failed: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


@extend_schema(
    request={
        'multipart/form-data': {
            'type': 'object',
            'properties': {
                'image': {
                    'type': 'string',
                    'format': 'binary',
                    'description': 'Image file to upload for chat message',
                }
            },
            'required': ['image']
        }
    },
    responses={
        200: inline_serializer(
            name='UploadImageResponse',
            fields={
                'image_url': serializers.URLField(),
                'filename': serializers.CharField(),
                'size': serializers.IntegerField(),
                'mime_type': serializers.CharField(),
            }
        )
    },
    summary="Upload chat image",
    description="Upload image for chat message (to be sent via WebSocket). Returns MinIO URL."
)
class UploadChatImageView(APIView):
    """
    Upload image for chat message
    Returns MinIO URL to be sent via WebSocket
    
    POST /api/ai/upload-image/
    """
    permission_classes = (IsAuthenticated,)
    
    def post(self, request):
        image_file = request.FILES.get('image')
        
        if not image_file:
            return Response(
                {'error': 'No image provided'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Validate image type
        valid_types = [
            'image/png', 'image/jpeg', 'image/jpg',
            'image/webp', 'image/heic', 'image/heif'
        ]
        if image_file.content_type not in valid_types:
            return Response(
                {'error': 'Invalid image format. Allowed: PNG, JPEG, WebP, HEIC, HEIF'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Validate size (max 50MB)
        max_size = 50 * 1024 * 1024
        if image_file.size > max_size:
            return Response(
                {'error': 'Image too large. Maximum size: 50MB'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            from django.core.files.storage import default_storage
            from django.conf import settings
            import uuid
            
            # Ensure bucket exists if using MinIO
            if getattr(settings, 'USE_MINIO', False):
                try:
                    from config.minio_service import get_minio_service
                    minio_service = get_minio_service()
                    bucket_name = getattr(settings, 'MINIO_BUCKET_NAME', 'jarvis-media')
                    minio_service.ensure_bucket_exists(bucket_name)
                except Exception as storage_error:
                    # Log but don't fail - storage might still work
                    import logging
                    logger = logging.getLogger(__name__)
                    logger.warning(f"Could not ensure MinIO bucket exists: {storage_error}")
            
            # Generate unique filename
            ext = image_file.name.split('.')[-1] if '.' in image_file.name else 'jpg'
            filename = f"chat_images/user_{request.user.id}/{uuid.uuid4()}.{ext}"
            
            # Save to storage (local file system by default, or MinIO if enabled)
            saved_path = default_storage.save(filename, image_file)
            image_url = default_storage.url(saved_path)
            
            # For local storage, ensure URL is relative and can be served by Django
            # For MinIO, the storage backend handles absolute URLs
            if not getattr(settings, 'USE_MINIO', False):
                # Local storage - URL should be relative like /media/chat_images/...
                # Django will serve it via MEDIA_URL
                if not image_url.startswith('/'):
                    # Make it relative if it's not already
                    image_url = f"/media/{saved_path}"
            
            return Response({
                'image_url': image_url,
                'filename': saved_path,
                'size': image_file.size,
                'mime_type': image_file.content_type,
            })
            
        except Exception as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Image upload failed: {str(e)}", exc_info=True)
            return Response(
                {'error': f'Upload failed: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
