"""
Tests for voice app - TDD approach
"""
from django.test import TestCase
from django.contrib.auth.models import User
from voice.models import VoiceCommand
from decimal import Decimal


class VoiceCommandModelTest(TestCase):
    """Test VoiceCommand model"""

    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )

    def test_create_voice_command(self):
        """Test creating a voice command"""
        cmd = VoiceCommand.objects.create(
            user=self.user,
            transcribed_text="Hello AI",
            command_type="question",
            response_text="Hello! How can I help you?",
            stt_method="backend_whisper",
            audio_duration=5.2,
            transcription_tokens=100,
            tts_characters=25,
            total_cost=Decimal('0.05')
        )
        
        self.assertEqual(cmd.user, self.user)
        self.assertEqual(cmd.transcribed_text, "Hello AI")
        self.assertEqual(cmd.command_type, "question")
        self.assertEqual(cmd.stt_method, "backend_whisper")

    def test_voice_command_string_representation(self):
        """Test VoiceCommand __str__ method"""
        cmd = VoiceCommand.objects.create(
            user=self.user,
            transcribed_text="Test command",
            command_type="question",
            stt_method="backend_whisper"
        )
        
        expected = f"{self.user.username} - Test command"
        self.assertEqual(str(cmd), expected)
