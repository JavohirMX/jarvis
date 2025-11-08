"""
Tests for profiles app - TDD approach
Testing UserProfile model, API endpoints, and settings management
"""
from django.test import TestCase
from django.contrib.auth.models import User
from django.urls import reverse
from rest_framework.test import APITestCase, APIClient
from rest_framework import status
from rest_framework_simplejwt.tokens import RefreshToken
from datetime import datetime, timedelta
from profiles.models import UserProfile
from django.conf import settings


class UserProfileModelTest(TestCase):
    """Test UserProfile model"""

    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )

    def test_profile_created_automatically_on_user_creation(self):
        """Test that a UserProfile is automatically created when a User is created"""
        self.assertTrue(hasattr(self.user, 'profile'))
        self.assertIsInstance(self.user.profile, UserProfile)

    def test_profile_default_values(self):
        """Test that UserProfile has correct default values"""
        profile = self.user.profile
        
        # Theme preferences
        self.assertEqual(profile.theme, 'dark')
        
        # AI settings
        self.assertEqual(profile.ai_response_length, 'medium')
        
        # Notification settings
        self.assertTrue(profile.notifications_enabled)
        self.assertTrue(profile.notification_sound)
        self.assertEqual(profile.notification_position, 'bottom-right')
        
        # Window preferences
        self.assertEqual(profile.window_opacity, 0.95)
        
        # Voice settings
        self.assertTrue(profile.voice_enabled)
        self.assertEqual(profile.voice_speed, 1.0)
        self.assertEqual(profile.voice_language, 'en-US')
        
        # Token usage
        self.assertEqual(profile.total_tokens_used, 0)
        self.assertEqual(profile.current_month_tokens, 0)
        self.assertEqual(profile.current_day_tokens, 0)
        self.assertEqual(profile.daily_token_limit, settings.DEFAULT_DAILY_TOKEN_LIMIT)
        self.assertEqual(profile.monthly_token_limit, settings.DEFAULT_MONTHLY_TOKEN_LIMIT)
        self.assertFalse(profile.is_premium_user)

    def test_profile_string_representation(self):
        """Test UserProfile __str__ method"""
        self.assertEqual(str(self.user.profile), f"Profile of {self.user.username}")

    def test_token_usage_increment(self):
        """Test incrementing token usage"""
        profile = self.user.profile
        profile.current_day_tokens = 100
        profile.current_month_tokens = 500
        profile.total_tokens_used = 5000
        profile.save()
        
        profile.refresh_from_db()
        self.assertEqual(profile.current_day_tokens, 100)
        self.assertEqual(profile.current_month_tokens, 500)
        self.assertEqual(profile.total_tokens_used, 5000)

    def test_premium_user_limits(self):
        """Test that premium users have higher limits"""
        profile = self.user.profile
        profile.is_premium_user = True
        profile.daily_token_limit = settings.PREMIUM_DAILY_TOKEN_LIMIT
        profile.monthly_token_limit = settings.PREMIUM_MONTHLY_TOKEN_LIMIT
        profile.save()
        
        profile.refresh_from_db()
        self.assertEqual(profile.daily_token_limit, settings.PREMIUM_DAILY_TOKEN_LIMIT)
        self.assertEqual(profile.monthly_token_limit, settings.PREMIUM_MONTHLY_TOKEN_LIMIT)


class UserProfileAPITest(APITestCase):
    """Test UserProfile API endpoints"""

    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.profile = self.user.profile
        
        # Get JWT token
        refresh = RefreshToken.for_user(self.user)
        self.access_token = str(refresh.access_token)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.access_token}')

    def test_get_profile_authenticated(self):
        """Test retrieving profile for authenticated user"""
        url = reverse('profile-detail')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['user']['username'], 'testuser')
        self.assertEqual(response.data['theme'], 'dark')
        self.assertIn('total_tokens_used', response.data)

    def test_get_profile_unauthenticated(self):
        """Test that unauthenticated users cannot access profile"""
        self.client.credentials()  # Remove authentication
        url = reverse('profile-detail')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_update_profile_partial(self):
        """Test partial update of profile (PATCH)"""
        url = reverse('profile-detail')
        data = {
            'theme': 'light',
            'ai_response_length': 'short',
            'notifications_enabled': False
        }
        response = self.client.patch(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.profile.refresh_from_db()
        self.assertEqual(self.profile.theme, 'light')
        self.assertEqual(self.profile.ai_response_length, 'short')
        self.assertFalse(self.profile.notifications_enabled)

    def test_update_profile_full(self):
        """Test full update of profile (PUT)"""
        url = reverse('profile-detail')
        data = {
            'theme': 'custom',
            'theme_custom_colors': {'primary': '#FF5733'},
            'ai_response_length': 'long',
            'notifications_enabled': True,
            'notification_sound': False,
            'notification_position': 'top-right',
            'window_opacity': 0.8,
            'voice_enabled': False,
            'preferred_voice': 'nova',
            'voice_speed': 1.2,
            'voice_language': 'es-ES'
        }
        response = self.client.put(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.profile.refresh_from_db()
        self.assertEqual(self.profile.theme, 'custom')
        self.assertEqual(self.profile.ai_response_length, 'long')
        self.assertFalse(self.profile.voice_enabled)
        self.assertEqual(self.profile.voice_speed, 1.2)

    def test_update_profile_invalid_choice(self):
        """Test updating profile with invalid choice value"""
        url = reverse('profile-detail')
        data = {'theme': 'invalid_theme'}
        response = self.client.patch(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_reset_profile_settings(self):
        """Test resetting profile to default settings"""
        # First, modify the profile
        self.profile.theme = 'light'
        self.profile.ai_response_length = 'long'
        self.profile.notifications_enabled = False
        self.profile.save()
        
        url = reverse('profile-reset')
        response = self.client.post(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.profile.refresh_from_db()
        
        # Check that settings are reset to defaults
        self.assertEqual(self.profile.theme, 'dark')
        self.assertEqual(self.profile.ai_response_length, 'medium')
        self.assertTrue(self.profile.notifications_enabled)

    def test_get_usage_statistics(self):
        """Test retrieving usage statistics"""
        # Set some usage data
        self.profile.current_day_tokens = 500
        self.profile.current_month_tokens = 5000
        self.profile.total_tokens_used = 50000
        self.profile.save()
        
        url = reverse('profile-usage')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['current_day_tokens'], 500)
        self.assertEqual(response.data['daily_remaining'], self.profile.daily_token_limit - 500)
        self.assertEqual(response.data['current_month_tokens'], 5000)
        self.assertEqual(response.data['total_tokens_used'], 50000)

    def test_cannot_modify_token_usage_directly(self):
        """Test that users cannot directly modify token usage through API"""
        url = reverse('profile-detail')
        data = {
            'current_day_tokens': 999999,
            'current_month_tokens': 999999,
            'total_tokens_used': 999999
        }
        response = self.client.patch(url, data, format='json')
        
        # Should succeed but token values shouldn't change
        self.profile.refresh_from_db()
        self.assertNotEqual(self.profile.current_day_tokens, 999999)

    def test_cannot_modify_limits_as_regular_user(self):
        """Test that regular users cannot modify their token limits"""
        url = reverse('profile-detail')
        data = {
            'daily_token_limit': 999999,
            'monthly_token_limit': 999999
        }
        response = self.client.patch(url, data, format='json')
        
        # Should succeed but limits shouldn't change
        self.profile.refresh_from_db()
        self.assertEqual(self.profile.daily_token_limit, settings.DEFAULT_DAILY_TOKEN_LIMIT)
        self.assertEqual(self.profile.monthly_token_limit, settings.DEFAULT_MONTHLY_TOKEN_LIMIT)


class UserProfileSignalTest(TestCase):
    """Test signals for automatic profile creation"""

    def test_profile_created_on_user_save(self):
        """Test that profile is created when new user is created"""
        user = User.objects.create_user(
            username='newuser',
            email='new@example.com',
            password='newpass123'
        )
        
        self.assertTrue(UserProfile.objects.filter(user=user).exists())
        profile = UserProfile.objects.get(user=user)
        self.assertEqual(profile.user, user)

    def test_profile_not_duplicated(self):
        """Test that saving an existing user doesn't create duplicate profile"""
        user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        
        initial_profile_count = UserProfile.objects.filter(user=user).count()
        self.assertEqual(initial_profile_count, 1)
        
        # Save user again
        user.email = 'updated@example.com'
        user.save()
        
        # Profile count should still be 1
        final_profile_count = UserProfile.objects.filter(user=user).count()
        self.assertEqual(final_profile_count, 1)
