from django.contrib.auth.models import User
from django.core.cache import cache
from django.test import override_settings
from rest_framework.test import APITestCase

LOCMEM = {'default': {'BACKEND': 'django.core.cache.backends.locmem.LocMemCache'}}


@override_settings(CACHES=LOCMEM)
class AuthEndpointTests(APITestCase):
    def setUp(self):
        cache.clear()
        User.objects.create_user('ann', 'Ann@Example.com', 'Str0ng-pass-123')

    def login(self, email, password='Str0ng-pass-123'):
        return self.client.post('/api/auth/login/', {'email': email, 'password': password}, format='json')

    def test_login_matches_email_ignoring_case(self):
        self.assertEqual(self.login('ann@example.com').status_code, 200)

    def test_unknown_email_and_wrong_password_look_the_same(self):
        wrong = self.login('Ann@example.com', 'nope-nope-nope')
        unknown = self.login('nobody@example.com')
        self.assertEqual(wrong.status_code, 400)
        self.assertEqual(wrong.json(), unknown.json())

    def test_register_rejects_email_differing_only_by_case(self):
        r = self.client.post('/api/auth/register/', {
            'username': 'ann2', 'email': 'ANN@example.com', 'password': 'Str0ng-pass-123'}, format='json')
        self.assertEqual(r.status_code, 400)
        self.assertIn('email', r.json())

    def test_login_is_throttled(self):
        from unittest import mock
        from rest_framework.throttling import SimpleRateThrottle
        with mock.patch.dict(SimpleRateThrottle.THROTTLE_RATES, {'auth': '3/min'}):
            codes = [self.login('ann@example.com', 'bad-bad-bad').status_code for _ in range(5)]
        self.assertEqual(codes[:3], [400, 400, 400])
        self.assertEqual(codes[-1], 429)

    def test_logout_does_not_leak_exception_text(self):
        tokens = self.login('ann@example.com').json()
        self.client.credentials(HTTP_AUTHORIZATION='Bearer ' + tokens['access'])
        r = self.client.post('/api/auth/logout/', {'refresh': 'garbage'}, format='json')
        self.assertEqual(r.status_code, 400)
        self.assertEqual(r.json(), {'error': 'Invalid or expired refresh token'})
