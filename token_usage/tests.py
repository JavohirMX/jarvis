"""
Tests for token_usage app - TDD approach
Testing TokenUsage model, UsageQuota model, API endpoints, and middleware
"""
from django.test import TestCase
from django.contrib.auth.models import User
from django.urls import reverse
from rest_framework.test import APITestCase, APIClient
from rest_framework import status
from rest_framework_simplejwt.tokens import RefreshToken
from datetime import date, datetime, timedelta
from decimal import Decimal
from token_usage.models import TokenUsage, UsageQuota
from profiles.models import UserProfile


class TokenUsageModelTest(TestCase):
    """Test TokenUsage model"""

    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )

    def test_create_token_usage_entry(self):
        """Test creating a TokenUsage entry"""
        usage = TokenUsage.objects.create(
            user=self.user,
            date=date.today(),
            feature_type='chat',
            ai_model_used='gpt-4',
            prompt_tokens=100,
            completion_tokens=200,
            total_tokens=300,
            estimated_cost=Decimal('0.015'),
            request_count=1
        )
        
        self.assertEqual(usage.user, self.user)
        self.assertEqual(usage.feature_type, 'chat')
        self.assertEqual(usage.total_tokens, 300)
        self.assertEqual(usage.request_count, 1)

    def test_token_usage_string_representation(self):
        """Test TokenUsage __str__ method"""
        usage = TokenUsage.objects.create(
            user=self.user,
            date=date.today(),
            feature_type='chat',
            ai_model_used='gpt-3.5-turbo',
            total_tokens=500
        )
        
        expected = f"{self.user.username} - {date.today()} - chat - 500 tokens"
        self.assertEqual(str(usage), expected)

    def test_aggregate_usage_by_date(self):
        """Test aggregating usage by date"""
        today = date.today()
        yesterday = today - timedelta(days=1)
        
        # Create multiple entries for today
        TokenUsage.objects.create(
            user=self.user, date=today, feature_type='chat',
            ai_model_used='gpt-4', total_tokens=100
        )
        TokenUsage.objects.create(
            user=self.user, date=today, feature_type='summarize',
            ai_model_used='gpt-4', total_tokens=150
        )
        
        # Create entry for yesterday
        TokenUsage.objects.create(
            user=self.user, date=yesterday, feature_type='chat',
            ai_model_used='gpt-4', total_tokens=200
        )
        
        # Check today's usage
        today_usage = TokenUsage.objects.filter(user=self.user, date=today)
        total_today = sum(u.total_tokens for u in today_usage)
        self.assertEqual(total_today, 250)

    def test_usage_by_feature_type(self):
        """Test filtering usage by feature type"""
        TokenUsage.objects.create(
            user=self.user, date=date.today(), feature_type='chat',
            ai_model_used='gpt-4', total_tokens=100
        )
        TokenUsage.objects.create(
            user=self.user, date=date.today(), feature_type='translate',
            ai_model_used='gpt-4', total_tokens=50
        )
        
        chat_usage = TokenUsage.objects.filter(user=self.user, feature_type='chat')
        self.assertEqual(chat_usage.count(), 1)
        self.assertEqual(chat_usage.first().total_tokens, 100)


class UsageQuotaModelTest(TestCase):
    """Test UsageQuota model"""

    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )

    def test_create_usage_quota(self):
        """Test creating a UsageQuota"""
        quota = UsageQuota.objects.create(
            user=self.user,
            quota_type='daily',
            limit=10000,
            used=500,
            reset_date=datetime.now() + timedelta(days=1)
        )
        
        self.assertEqual(quota.user, self.user)
        self.assertEqual(quota.quota_type, 'daily')
        self.assertEqual(quota.limit, 10000)
        self.assertEqual(quota.used, 500)
        self.assertTrue(quota.is_active)

    def test_quota_string_representation(self):
        """Test UsageQuota __str__ method"""
        quota = UsageQuota.objects.create(
            user=self.user,
            quota_type='monthly',
            limit=100000,
            used=25000,
            reset_date=datetime.now() + timedelta(days=30)
        )
        
        expected = f"{self.user.username} - monthly quota: 25000/100000"
        self.assertEqual(str(quota), expected)

    def test_quota_remaining(self):
        """Test calculating remaining quota"""
        quota = UsageQuota.objects.create(
            user=self.user,
            quota_type='daily',
            limit=10000,
            used=3000,
            reset_date=datetime.now() + timedelta(days=1)
        )
        
        remaining = quota.limit - quota.used
        self.assertEqual(remaining, 7000)

    def test_quota_exceeded(self):
        """Test detecting when quota is exceeded"""
        quota = UsageQuota.objects.create(
            user=self.user,
            quota_type='daily',
            limit=10000,
            used=10500,
            reset_date=datetime.now() + timedelta(days=1)
        )
        
        self.assertGreater(quota.used, quota.limit)

    def test_increment_quota_usage(self):
        """Test incrementing quota usage"""
        quota = UsageQuota.objects.create(
            user=self.user,
            quota_type='daily',
            limit=10000,
            used=1000,
            reset_date=datetime.now() + timedelta(days=1)
        )
        
        quota.used += 500
        quota.save()
        
        quota.refresh_from_db()
        self.assertEqual(quota.used, 1500)


class TokenUsageAPITest(APITestCase):
    """Test TokenUsage API endpoints"""

    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        
        # Get JWT token
        refresh = RefreshToken.for_user(self.user)
        self.access_token = str(refresh.access_token)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.access_token}')
        
        # Create some token usage data
        today = date.today()
        yesterday = today - timedelta(days=1)
        
        TokenUsage.objects.create(
            user=self.user, date=today, feature_type='chat',
            ai_model_used='gpt-4', prompt_tokens=100, completion_tokens=200,
            total_tokens=300, estimated_cost=Decimal('0.015'), request_count=1
        )
        TokenUsage.objects.create(
            user=self.user, date=today, feature_type='summarize',
            ai_model_used='gpt-4', prompt_tokens=50, completion_tokens=100,
            total_tokens=150, estimated_cost=Decimal('0.0075'), request_count=1
        )
        TokenUsage.objects.create(
            user=self.user, date=yesterday, feature_type='chat',
            ai_model_used='gpt-3.5-turbo', prompt_tokens=200, completion_tokens=300,
            total_tokens=500, estimated_cost=Decimal('0.005'), request_count=1
        )

    def test_get_usage_stats(self):
        """Test retrieving usage statistics"""
        url = reverse('usage-stats')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('total_tokens', response.data)
        self.assertIn('total_cost', response.data)
        self.assertIn('by_feature', response.data)
        self.assertIn('by_model', response.data)

    def test_get_usage_history(self):
        """Test retrieving usage history"""
        url = reverse('usage-history')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIsInstance(response.data['results'], list)
        self.assertGreater(len(response.data['results']), 0)

    def test_filter_usage_by_date(self):
        """Test filtering usage history by date"""
        url = reverse('usage-history')
        today = date.today()
        response = self.client.get(url, {'date': today.isoformat()})
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        for entry in response.data['results']:
            self.assertEqual(entry['date'], today.isoformat())

    def test_filter_usage_by_feature(self):
        """Test filtering usage history by feature type"""
        url = reverse('usage-history')
        response = self.client.get(url, {'feature_type': 'chat'})
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        for entry in response.data['results']:
            self.assertEqual(entry['feature_type'], 'chat')

    def test_get_quotas(self):
        """Test retrieving user quotas"""
        url = reverse('usage-quotas')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('daily', response.data)
        self.assertIn('monthly', response.data)

    def test_get_cost_breakdown(self):
        """Test retrieving cost breakdown"""
        url = reverse('usage-cost')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('total_cost', response.data)
        self.assertIn('by_feature', response.data)
        self.assertIn('by_model', response.data)

    def test_usage_stats_unauthenticated(self):
        """Test that unauthenticated users cannot access usage stats"""
        self.client.credentials()  # Remove authentication
        url = reverse('usage-stats')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


class UsageTrackingTest(TestCase):
    """Test usage tracking functionality"""

    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.profile = self.user.profile

    def test_track_token_usage(self):
        """Test tracking token usage creates TokenUsage entry"""
        initial_count = TokenUsage.objects.filter(user=self.user).count()
        
        TokenUsage.objects.create(
            user=self.user,
            date=date.today(),
            feature_type='chat',
            ai_model_used='gpt-4',
            prompt_tokens=100,
            completion_tokens=200,
            total_tokens=300,
            estimated_cost=Decimal('0.015'),
            request_count=1
        )
        
        final_count = TokenUsage.objects.filter(user=self.user).count()
        self.assertEqual(final_count, initial_count + 1)

    def test_profile_token_sync(self):
        """Test that profile tokens can be updated"""
        self.profile.increment_token_usage(500)
        
        self.profile.refresh_from_db()
        self.assertEqual(self.profile.current_day_tokens, 500)
        self.assertEqual(self.profile.current_month_tokens, 500)
        self.assertEqual(self.profile.total_tokens_used, 500)

    def test_multiple_requests_aggregate(self):
        """Test that multiple requests aggregate correctly"""
        tokens_list = [100, 200, 150, 300]
        
        for tokens in tokens_list:
            self.profile.increment_token_usage(tokens)
        
        self.profile.refresh_from_db()
        self.assertEqual(self.profile.current_day_tokens, sum(tokens_list))
