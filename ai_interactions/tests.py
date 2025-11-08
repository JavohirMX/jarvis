"""
Tests for ai_interactions app - TDD approach
Testing Conversation, AIMessage, AIMemory models and AI endpoints
"""
from django.test import TestCase
from django.contrib.auth.models import User
from django.urls import reverse
from rest_framework.test import APITestCase, APIClient
from rest_framework import status
from rest_framework_simplejwt.tokens import RefreshToken
from datetime import date
from decimal import Decimal
from ai_interactions.models import Conversation, AIMessage, AIMemory


class ConversationModelTest(TestCase):
    """Test Conversation model"""

    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )

    def test_create_conversation(self):
        """Test creating a conversation"""
        conv = Conversation.objects.create(
            user=self.user,
            title="Test Conversation"
        )
        
        self.assertEqual(conv.user, self.user)
        self.assertEqual(conv.title, "Test Conversation")
        self.assertTrue(conv.is_active)
        self.assertEqual(conv.total_tokens_used, 0)
        self.assertEqual(conv.message_count, 0)

    def test_conversation_string_representation(self):
        """Test Conversation __str__ method"""
        conv = Conversation.objects.create(
            user=self.user,
            title="My Conversation"
        )
        
        expected = f"{self.user.username} - My Conversation"
        self.assertEqual(str(conv), expected)


class AIMessageModelTest(TestCase):
    """Test AIMessage model"""

    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.conversation = Conversation.objects.create(
            user=self.user,
            title="Test Conv"
        )

    def test_create_ai_message(self):
        """Test creating an AI message"""
        msg = AIMessage.objects.create(
            conversation=self.conversation,
            role='user',
            content='Hello AI',
            ai_model_used='gpt-4',
            prompt_tokens=10,
            completion_tokens=20,
            total_tokens=30
        )
        
        self.assertEqual(msg.conversation, self.conversation)
        self.assertEqual(msg.role, 'user')
        self.assertEqual(msg.content, 'Hello AI')
        self.assertEqual(msg.total_tokens, 30)

    def test_message_roles(self):
        """Test different message roles"""
        roles = ['user', 'assistant', 'system']
        
        for role in roles:
            msg = AIMessage.objects.create(
                conversation=self.conversation,
                role=role,
                content=f'Message from {role}',
                ai_model_used='gpt-4'
            )
            self.assertEqual(msg.role, role)


class AIMemoryModelTest(TestCase):
    """Test AIMemory model"""

    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )

    def test_create_ai_memory(self):
        """Test creating AI memory"""
        memory = AIMemory.objects.create(
            user=self.user,
            key_facts={'name': 'John', 'preference': 'concise answers'}
        )
        
        self.assertEqual(memory.user, self.user)
        self.assertIn('name', memory.key_facts)
        self.assertEqual(memory.key_facts['name'], 'John')

    def test_memory_string_representation(self):
        """Test AIMemory __str__ method"""
        memory = AIMemory.objects.create(
            user=self.user,
            key_facts={'test': 'data'}
        )
        
        expected = f"AI Memory for {self.user.username}"
        self.assertEqual(str(memory), expected)


class AIInteractionsAPITest(APITestCase):
    """Test AI Interactions API endpoints"""

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
        
        # Create test conversation
        self.conversation = Conversation.objects.create(
            user=self.user,
            title="Test Conversation"
        )

    def test_list_conversations(self):
        """Test listing user's conversations"""
        url = reverse('conversation-list')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertGreater(len(response.data['results']), 0)

    def test_get_conversation_detail(self):
        """Test retrieving a specific conversation"""
        url = reverse('conversation-detail', kwargs={'pk': self.conversation.id})
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['title'], "Test Conversation")

    def test_delete_conversation(self):
        """Test deleting a conversation"""
        url = reverse('conversation-detail', kwargs={'pk': self.conversation.id})
        response = self.client.delete(url)
        
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Conversation.objects.filter(id=self.conversation.id).exists())

    def test_get_memory(self):
        """Test retrieving user's AI memory"""
        # Create memory
        AIMemory.objects.create(
            user=self.user,
            key_facts={'name': 'Test User'}
        )
        
        url = reverse('ai-memory')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('name', response.data['key_facts'])

    def test_unauthenticated_access_denied(self):
        """Test that unauthenticated users cannot access endpoints"""
        self.client.credentials()  # Remove authentication
        url = reverse('conversation-list')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
