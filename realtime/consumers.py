"""
WebSocket consumers for real-time communication
"""
import json
import asyncio
from typing import AsyncGenerator
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from datetime import date
from decimal import Decimal


class AIAssistantConsumer(AsyncWebsocketConsumer):
    """
    WebSocket consumer for AI Assistant real-time communication
    
    Handles:
    - AI response streaming
    - Token usage updates
    - Quota warnings
    - Voice command processing
    - Clipboard context (not stored)
    """
    
    async def connect(self):
        """Handle WebSocket connection"""
        self.user = self.scope["user"]
        
        # Check if user is authenticated
        if self.user.is_anonymous:
            await self.close()
            return
        
        # Create a user-specific channel group
        self.room_group_name = f'assistant_{self.user.id}'
        
        # Join room group
        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )
        
        await self.accept()
        
        # Send welcome message
        await self.send(text_data=json.dumps({
            'type': 'connection',
            'message': 'Connected to AI Assistant'
        }))
    
    async def disconnect(self, close_code):
        """Handle WebSocket disconnection"""
        # Leave room group
        if hasattr(self, 'room_group_name'):
            await self.channel_layer.group_discard(
                self.room_group_name,
                self.channel_name
            )
    
    async def receive(self, text_data):
        """
        Receive message from WebSocket
        
        Expected message format:
        {
            "type": "ai_request" | "voice_command" | "clipboard_context",
            "data": {...}
        }
        """
        try:
            data = json.loads(text_data)
            message_type = data.get('type')
            
            if message_type == 'ai_request':
                await self.handle_ai_request(data)
            elif message_type == 'voice_command':
                await self.handle_voice_command(data)
            elif message_type == 'clipboard_context':
                await self.handle_clipboard_context(data)
            else:
                await self.send(text_data=json.dumps({
                    'type': 'error',
                    'message': f'Unknown message type: {message_type}'
                }))
        
        except json.JSONDecodeError:
            await self.send(text_data=json.dumps({
                'type': 'error',
                'message': 'Invalid JSON'
            }))
        except Exception as e:
            await self.send(text_data=json.dumps({
                'type': 'error',
                'message': str(e)
            }))
    
    async def handle_ai_request(self, data):
        """Handle AI request and stream response"""
        message = data.get('data', {}).get('message', '').strip()
        conversation_id = data.get('data', {}).get('conversation_id')
        context = data.get('data', {}).get('context', {})
        provider = data.get('data', {}).get('provider')  # Optional provider override
        image_url = data.get('data', {}).get('image_url')  # Image uploaded via HTTP
        image_data = data.get('data', {}).get('image_data')  # Base64 image (alternative)
        
        if not message:
            await self.send(text_data=json.dumps({
                'type': 'error',
                'message': 'Message is required'
            }))
            return
        
        # Check quota
        profile = await self.get_user_profile()
        if not profile.has_daily_quota_remaining():
            await self.send(text_data=json.dumps({
                'type': 'error',
                'message': 'Daily quota exceeded',
                'code': 'QUOTA_EXCEEDED'
            }))
            return
        
        try:
            # Get or create conversation
            if conversation_id:
                conversation = await self.get_conversation(conversation_id)
                if not conversation:
                    await self.send(text_data=json.dumps({
                        'type': 'error',
                        'message': 'Conversation not found',
                        'code': 'CONVERSATION_NOT_FOUND'
                    }))
                    return
            else:
                # Create new conversation with first message as title
                title = message[:50] + ('...' if len(message) > 50 else '')
                conversation = await self.create_conversation(title)
            
            # Save user message (with optional image)
            user_message = await self.save_user_message(conversation, message, context, image_url)
            
            # Get conversation history
            history = await self.get_conversation_history(conversation)
            
            # Send start signal
            await self.send(text_data=json.dumps({
                'type': 'ai_response',
                'status': 'streaming',
                'conversation_id': conversation.id,
                'message_id': user_message.id
            }))
            
            # Initialize AI service
            ai_service = await self.get_ai_service(provider)
            
            # Stream AI response
            full_response = ""
            prompt_tokens = 0
            completion_tokens = 0
            total_tokens = 0
            model_used = None
            
            try:
                # Stream chunks from AI service
                async for chunk in self.stream_ai_response(ai_service, message, context, history):
                    full_response += chunk
                    # Send each chunk to WebSocket
                    await self.send(text_data=json.dumps({
                        'type': 'ai_response_chunk',
                        'chunk': chunk,
                        'status': 'streaming'
                    }))
                
                # Get token usage from the response (we need to make a final call or track it)
                # For now, we'll estimate or get it from a final non-streaming call
                # In production, you'd track tokens as they come in
                token_info = await self.get_token_usage(ai_service, message, context, history, full_response)
                prompt_tokens = token_info['prompt_tokens']
                completion_tokens = token_info['completion_tokens']
                total_tokens = token_info['total_tokens']
                model_used = token_info['model']
                
            except Exception as e:
                await self.send(text_data=json.dumps({
                    'type': 'error',
                    'message': f'AI processing failed: {str(e)}',
                    'code': 'AI_ERROR'
                }))
                return
            
            # Save AI response to database
            ai_message = await self.save_ai_response(
                conversation, 
                full_response, 
                model_used or 'gpt-4',
                prompt_tokens,
                completion_tokens,
                total_tokens
            )
            
            # Update conversation stats
            await self.update_conversation_stats(conversation)
            
            # Update usage tracking
            await self.update_usage_tracking(
                model_used or 'gpt-4',
                prompt_tokens,
                completion_tokens,
                total_tokens
            )
            
            # Send completion signal with token info
            await self.send(text_data=json.dumps({
                'type': 'ai_response',
                'status': 'complete',
                'message': full_response,
                'message_id': ai_message.id,
                'conversation_id': conversation.id,
                'tokens': {
                    'prompt': prompt_tokens,
                    'completion': completion_tokens,
                    'total': total_tokens
                }
            }))
            
            # Send token usage update
            await self.send_token_usage_update()
            
        except Exception as e:
            await self.send(text_data=json.dumps({
                'type': 'error',
                'message': f'Request processing failed: {str(e)}',
                'code': 'PROCESSING_ERROR'
            }))
    
    async def handle_voice_command(self, data):
        """Handle voice command processing"""
        transcribed_text = data.get('data', {}).get('transcribed_text', '')
        
        await self.send(text_data=json.dumps({
            'type': 'voice_response',
            'status': 'processing',
            'transcribed_text': transcribed_text
        }))
        
        # TODO: Implement voice command processing
        # For now, echo the transcription
        await self.send(text_data=json.dumps({
            'type': 'voice_response',
            'status': 'complete',
            'response': f'Understood: {transcribed_text}'
        }))
    
    async def handle_clipboard_context(self, data):
        """Handle clipboard context (not stored, just used for AI context)"""
        # Clipboard content is received but not stored, just acknowledged
        # It will be used as context in future AI requests
        
        # Acknowledge receipt
        await self.send(text_data=json.dumps({
            'type': 'clipboard_acknowledged',
            'message': 'Clipboard context received'
        }))
    
    async def send_token_usage_update(self):
        """Send token usage update to client"""
        profile = await self.get_user_profile()
        
        await self.send(text_data=json.dumps({
            'type': 'token_usage',
            'daily_used': profile.current_day_tokens,
            'daily_limit': profile.daily_token_limit,
            'daily_remaining': profile.daily_tokens_remaining(),
            'monthly_used': profile.current_month_tokens,
            'monthly_limit': profile.monthly_token_limit,
        }))
        
        # Check if approaching limits
        daily_percentage = (profile.current_day_tokens / profile.daily_token_limit) * 100
        if daily_percentage >= 90:
            await self.send(text_data=json.dumps({
                'type': 'quota_warning',
                'level': 'daily',
                'percentage_used': daily_percentage,
                'message': f'You have used {daily_percentage:.1f}% of your daily quota'
            }))
    
    @database_sync_to_async
    def get_user_profile(self):
        """Get user profile from database"""
        return self.user.profile
    
    @database_sync_to_async
    def get_conversation(self, conversation_id):
        """Get conversation by ID for current user"""
        from ai_interactions.models import Conversation
        try:
            return Conversation.objects.get(id=conversation_id, user=self.user)
        except Conversation.DoesNotExist:
            return None
    
    @database_sync_to_async
    def create_conversation(self, title):
        """Create a new conversation"""
        from ai_interactions.models import Conversation
        return Conversation.objects.create(user=self.user, title=title)
    
    @database_sync_to_async
    def save_user_message(self, conversation, message, context, image_url=None):
        """Save user message to database"""
        from ai_interactions.models import AIMessage
        msg = AIMessage.objects.create(
            conversation=conversation,
            role='user',
            content=message,
            context_data=context,
            ai_model_used='gpt-4',  # Will be updated from actual response
            prompt_tokens=0,
            completion_tokens=0,
            total_tokens=0
        )
        
        # If image_url is provided, store it
        if image_url:
            msg.image_url = image_url
            msg.save(update_fields=['image_url'])
        
        return msg
    
    @database_sync_to_async
    def save_ai_response(self, conversation, content, model, prompt_tokens, completion_tokens, total_tokens):
        """Save AI response to database"""
        from ai_interactions.models import AIMessage
        return AIMessage.objects.create(
            conversation=conversation,
            role='assistant',
            content=content,
            ai_model_used=model,
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
            total_tokens=total_tokens
        )
    
    @database_sync_to_async
    def get_conversation_history(self, conversation):
        """Get conversation history for context"""
        recent_messages = conversation.messages.order_by('created_at')[:20]
        return [
            {'role': msg.role, 'content': msg.content}
            for msg in recent_messages
        ]
    
    @database_sync_to_async
    def update_conversation_stats(self, conversation):
        """Update conversation statistics"""
        conversation.update_stats()
    
    @database_sync_to_async
    def update_usage_tracking(self, model, prompt_tokens, completion_tokens, total_tokens):
        """Update token usage in profile and create TokenUsage record"""
        from token_usage.models import TokenUsage
        
        # Update profile
        profile = self.user.profile
        profile.increment_token_usage(total_tokens)
        
        # Create TokenUsage record
        TokenUsage.objects.create(
            user=self.user,
            date=date.today(),
            feature_type='chat',
            ai_model_used=model,
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
            total_tokens=total_tokens,
            estimated_cost=Decimal('0.001') * total_tokens,  # Will be calculated properly by provider
            request_count=1
        )
    
    async def get_ai_service(self, provider=None):
        """Get AI service instance (sync wrapper)"""
        from ai_interactions.services import AIService
        
        def create_service():
            return AIService(user=self.user, provider=provider)
        
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, create_service)
    
    async def stream_ai_response(
        self, 
        ai_service, 
        message: str, 
        context: dict, 
        history: list
    ) -> AsyncGenerator[str, None]:
        """
        Stream AI response chunks asynchronously
        
        This wraps the sync generator from AIService.stream_chat()
        and converts it to an async generator using a queue
        """
        queue = asyncio.Queue()
        loop = asyncio.get_event_loop()
        error = None
        
        def run_stream():
            """Run sync stream_chat in thread and put chunks in queue"""
            nonlocal error
            try:
                stream = ai_service.stream_chat(
                    message=message,
                    context=context,
                    conversation_history=history,
                    temperature=0.7,
                    max_tokens=None
                )
                
                for chunk in stream:
                    # Put chunk in queue (this is thread-safe)
                    loop.call_soon_threadsafe(queue.put_nowait, chunk)
                
                # Signal completion
                loop.call_soon_threadsafe(queue.put_nowait, None)
            except Exception as e:
                error = e
                loop.call_soon_threadsafe(queue.put_nowait, None)
        
        # Start streaming in background thread
        loop.run_in_executor(None, run_stream)
        
        # Yield chunks from queue
        while True:
            chunk = await queue.get()
            if chunk is None:
                # Check if there was an error
                if error:
                    raise error
                break
            yield chunk
    
    async def get_token_usage(self, ai_service, message, context, history, full_response):
        """
        Get token usage information by counting tokens in the actual messages
        """
        def get_usage():
            # Build messages the same way as stream_chat
            messages = ai_service._build_messages(message, context, history)
            
            # Count tokens in the full prompt (all messages combined)
            prompt_text = '\n'.join([f"{msg.role}: {msg.content}" for msg in messages])
            prompt_tokens = ai_service.count_tokens(prompt_text)
            
            # Count tokens in the completion
            completion_tokens = ai_service.count_tokens(full_response)
            total_tokens = prompt_tokens + completion_tokens
            
            return {
                'prompt_tokens': prompt_tokens,
                'completion_tokens': completion_tokens,
                'total_tokens': total_tokens,
                'model': ai_service.provider.model
            }
        
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, get_usage)
    
    # Handle messages from channel layer
    async def ai_response_chunk(self, event):
        """Send AI response chunk to WebSocket"""
        await self.send(text_data=json.dumps(event['data']))
    
    async def token_usage_update(self, event):
        """Send token usage update to WebSocket"""
        await self.send(text_data=json.dumps(event['data']))
    
    async def quota_warning(self, event):
        """Send quota warning to WebSocket"""
        await self.send(text_data=json.dumps(event['data']))

