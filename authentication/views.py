from typing import Any
from rest_framework import generics, status, serializers as drf_serializers
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework_simplejwt.views import TokenObtainPairView
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework.views import APIView
from rest_framework.request import Request
from django.contrib.auth.models import User
from drf_spectacular.utils import extend_schema, inline_serializer

from .serializers import RegisterSerializer, UserSerializer, EmailTokenObtainPairSerializer


class RegisterView(generics.CreateAPIView):
    """
    API endpoint for user registration
    POST /api/auth/register/
    """
    queryset = User.objects.all()
    permission_classes = (AllowAny,)
    serializer_class = RegisterSerializer

    def create(self, request: Request, *args: Any, **kwargs: Any) -> Response:
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        
        # Generate tokens for the new user
        refresh = RefreshToken.for_user(user)
        
        return Response({
            'user': UserSerializer(user).data,
            'tokens': {
                'refresh': str(refresh),
                'access': str(refresh.access_token),
            },
            'message': 'User registered successfully'
        }, status=status.HTTP_201_CREATED)


@extend_schema(
    request=inline_serializer(
        name='LoginRequest',
        fields={
            'email': drf_serializers.EmailField(),
            'password': drf_serializers.CharField(write_only=True)
        }
    ),
    responses={
        200: inline_serializer(
            name='LoginResponse',
            fields={
                'refresh': drf_serializers.CharField(),
                'access': drf_serializers.CharField()
            }
        )
    }
)
class LoginView(TokenObtainPairView):
    """
    API endpoint for user login
    POST /api/auth/login/
    Authenticates with email and password instead of username
    """
    permission_classes = (AllowAny,)
    serializer_class = EmailTokenObtainPairSerializer


class LogoutSerializer(drf_serializers.Serializer):
    """Serializer for logout request"""
    refresh = drf_serializers.CharField()


@extend_schema(
    request=LogoutSerializer,
    responses={
        200: inline_serializer(
            name='LogoutResponse',
            fields={'message': drf_serializers.CharField()}
        )
    }
)
class LogoutView(APIView):
    """
    API endpoint for user logout (blacklist refresh token)
    POST /api/auth/logout/
    """
    permission_classes = (IsAuthenticated,)
    serializer_class = LogoutSerializer

    def post(self, request: Request) -> Response:
        try:
            refresh_token = request.data.get("refresh")
            if not refresh_token:
                return Response(
                    {"error": "Refresh token is required"},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            token = RefreshToken(refresh_token)
            token.blacklist()
            
            return Response(
                {"message": "Logout successful"},
                status=status.HTTP_200_OK
            )
        except Exception as e:
            return Response(
                {"error": str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )


class UserDetailView(generics.RetrieveAPIView):
    """
    API endpoint to get current user details
    GET /api/auth/user/
    """
    permission_classes = (IsAuthenticated,)
    serializer_class = UserSerializer

    def get_object(self) -> User:
        return self.request.user
