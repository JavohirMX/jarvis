# WebSocket + Image Upload Guide

## Overview

Your chat uses WebSockets for real-time communication. Images can be handled in two ways:

1. **Hybrid Approach (RECOMMENDED)**: Upload via HTTP, send URL via WebSocket
2. **Base64 Approach**: Encode and send via WebSocket (not recommended for large images)

---

## ✅ Solution 1: Hybrid Approach (RECOMMENDED)

### How It Works

```
1. User selects image → Upload to `/api/ai/upload-image/` (HTTP)
2. Backend saves to MinIO → Returns image URL
3. Send message via WebSocket with image_url
4. Backend processes message with image
```

### Backend: Create Image Upload Endpoint

**File: `ai_interactions/views.py`**

Add this new view:

```python
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from django.core.files.storage import default_storage
import uuid

class UploadChatImageView(APIView):
    """
    Upload image for chat message
    Returns MinIO URL to be sent via WebSocket
    """
    permission_classes = (IsAuthenticated,)
    
    def post(self, request):
        image_file = request.FILES.get('image')
        
        if not image_file:
            return Response(
                {'error': 'No image provided'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Validate image
        valid_types = ['image/png', 'image/jpeg', 'image/jpg', 'image/webp', 'image/heic']
        if image_file.content_type not in valid_types:
            return Response(
                {'error': 'Invalid image format'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Max 50MB
        if image_file.size > 50 * 1024 * 1024:
            return Response(
                {'error': 'Image too large (max 50MB)'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            # Generate unique filename
            ext = image_file.name.split('.')[-1]
            filename = f"chat_images/user_{request.user.id}/{uuid.uuid4()}.{ext}"
            
            # Save to MinIO
            saved_path = default_storage.save(filename, image_file)
            image_url = default_storage.url(saved_path)
            
            return Response({
                'image_url': image_url,
                'filename': saved_path,
                'size': image_file.size,
                'mime_type': image_file.content_type,
            })
            
        except Exception as e:
            return Response(
                {'error': f'Upload failed: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
```

**File: `ai_interactions/urls.py`**

Add route:

```python
from django.urls import path
from . import views

urlpatterns = [
    # ... existing routes ...
    path('upload-image/', views.UploadChatImageView.as_view(), name='upload-chat-image'),
]
```

### React Frontend: Complete Implementation

```jsx
import React, { useState, useEffect, useRef } from 'react';
import axios from 'axios';

const WebSocketChat = () => {
  const [messages, setMessages] = useState([]);
  const [inputMessage, setInputMessage] = useState('');
  const [selectedImage, setSelectedImage] = useState(null);
  const [imagePreview, setImagePreview] = useState(null);
  const [uploadedImageUrl, setUploadedImageUrl] = useState(null);
  const [uploading, setUploading] = useState(false);
  const [connected, setConnected] = useState(false);
  const wsRef = useRef(null);

  const API_URL = 'http://localhost:8000';
  const WS_URL = 'ws://localhost:8000';
  const TOKEN = localStorage.getItem('accessToken');

  // Initialize WebSocket
  useEffect(() => {
    connectWebSocket();
    return () => {
      if (wsRef.current) {
        wsRef.current.close();
      }
    };
  }, []);

  const connectWebSocket = () => {
    const ws = new WebSocket(`${WS_URL}/ws/assistant/?token=${TOKEN}`);

    ws.onopen = () => {
      console.log('WebSocket connected');
      setConnected(true);
    };

    ws.onmessage = (event) => {
      const data = JSON.parse(event.data);
      handleWebSocketMessage(data);
    };

    ws.onclose = () => {
      console.log('WebSocket disconnected');
      setConnected(false);
      // Reconnect after 3 seconds
      setTimeout(connectWebSocket, 3000);
    };

    ws.onerror = (error) => {
      console.error('WebSocket error:', error);
    };

    wsRef.current = ws;
  };

  const handleWebSocketMessage = (data) => {
    switch (data.type) {
      case 'connection':
        console.log('Connected:', data.message);
        break;

      case 'ai_response':
        if (data.status === 'streaming') {
          // Start of streaming response
          setMessages(prev => [...prev, {
            role: 'assistant',
            content: '',
            streaming: true,
          }]);
        } else if (data.status === 'complete') {
          // Complete response
          setMessages(prev => {
            const newMessages = [...prev];
            const lastMsg = newMessages[newMessages.length - 1];
            if (lastMsg && lastMsg.streaming) {
              lastMsg.content = data.message;
              lastMsg.streaming = false;
              lastMsg.tokens = data.tokens;
            }
            return newMessages;
          });
        }
        break;

      case 'ai_response_chunk':
        // Stream chunk
        setMessages(prev => {
          const newMessages = [...prev];
          const lastMsg = newMessages[newMessages.length - 1];
          if (lastMsg && lastMsg.streaming) {
            lastMsg.content += data.chunk;
          }
          return [...newMessages];
        });
        break;

      case 'error':
        alert(`Error: ${data.message}`);
        break;
    }
  };

  const handleImageSelect = (e) => {
    const file = e.target.files[0];
    if (!file) return;

    // Validate
    if (!file.type.startsWith('image/')) {
      alert('Please select an image file');
      return;
    }

    if (file.size > 50 * 1024 * 1024) {
      alert('Image must be less than 50MB');
      return;
    }

    setSelectedImage(file);

    // Create preview
    const reader = new FileReader();
    reader.onload = (e) => setImagePreview(e.target.result);
    reader.readAsDataURL(file);
  };

  const uploadImage = async () => {
    if (!selectedImage) return null;

    setUploading(true);

    try {
      const formData = new FormData();
      formData.append('image', selectedImage);

      const response = await axios.post(
        `${API_URL}/api/ai/upload-image/`,
        formData,
        {
          headers: {
            'Authorization': `Bearer ${TOKEN}`,
            'Content-Type': 'multipart/form-data',
          },
        }
      );

      return response.data.image_url;

    } catch (error) {
      console.error('Upload error:', error);
      alert('Failed to upload image');
      return null;
    } finally {
      setUploading(false);
    }
  };

  const sendMessage = async () => {
    if (!inputMessage.trim() && !selectedImage) return;
    if (!connected) {
      alert('Not connected to server');
      return;
    }

    let imageUrl = null;

    // Upload image first if selected
    if (selectedImage) {
      imageUrl = await uploadImage();
      if (!imageUrl) return; // Upload failed
    }

    // Add user message to UI
    const userMessage = {
      role: 'user',
      content: inputMessage,
      image_url: imageUrl,
      image_preview: imagePreview,
    };
    setMessages(prev => [...prev, userMessage]);

    // Send via WebSocket
    const wsMessage = {
      type: 'ai_request',
      data: {
        message: inputMessage || 'What\'s in this image?',
        image_url: imageUrl, // MinIO URL
        provider: imageUrl ? 'gemini' : undefined, // Use Gemini for images
        context: {},
      },
    };

    wsRef.current.send(JSON.stringify(wsMessage));

    // Clear inputs
    setInputMessage('');
    setSelectedImage(null);
    setImagePreview(null);
    setUploadedImageUrl(null);
  };

  const handleKeyPress = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      sendMessage();
    }
  };

  return (
    <div className="flex flex-col h-screen max-w-4xl mx-auto">
      {/* Connection Status */}
      <div className={`p-2 text-center ${connected ? 'bg-green-100' : 'bg-red-100'}`}>
        {connected ? '🟢 Connected' : '🔴 Disconnected'}
      </div>

      {/* Messages */}
      <div className="flex-1 overflow-y-auto p-4 space-y-4">
        {messages.map((msg, idx) => (
          <div
            key={idx}
            className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}
          >
            <div
              className={`max-w-[70%] p-3 rounded-lg ${
                msg.role === 'user'
                  ? 'bg-blue-500 text-white'
                  : 'bg-gray-200 text-black'
              }`}
            >
              {/* Image */}
              {msg.image_url && (
                <img
                  src={msg.image_url}
                  alt="attachment"
                  className="max-w-full rounded mb-2 max-h-64"
                />
              )}
              {msg.image_preview && !msg.image_url && (
                <img
                  src={msg.image_preview}
                  alt="preview"
                  className="max-w-full rounded mb-2 max-h-64"
                />
              )}

              {/* Text */}
              <p className="whitespace-pre-wrap">{msg.content}</p>
              
              {/* Streaming indicator */}
              {msg.streaming && (
                <span className="inline-block w-2 h-4 bg-current animate-pulse ml-1"></span>
              )}

              {/* Tokens */}
              {msg.tokens && (
                <p className="text-xs mt-1 opacity-70">
                  {msg.tokens.total} tokens
                </p>
              )}
            </div>
          </div>
        ))}
      </div>

      {/* Input Area */}
      <div className="border-t p-4 bg-white">
        {/* Image Preview */}
        {imagePreview && (
          <div className="mb-2 relative inline-block">
            <img
              src={imagePreview}
              alt="preview"
              className="max-h-32 rounded border"
            />
            <button
              onClick={() => {
                setSelectedImage(null);
                setImagePreview(null);
              }}
              className="absolute -top-2 -right-2 bg-red-500 text-white rounded-full w-6 h-6"
            >
              ✕
            </button>
            {uploading && (
              <div className="absolute inset-0 bg-black bg-opacity-50 flex items-center justify-center rounded">
                <span className="text-white">Uploading...</span>
              </div>
            )}
          </div>
        )}

        {/* Input */}
        <div className="flex gap-2">
          <label className="cursor-pointer px-3 py-2 bg-gray-200 rounded hover:bg-gray-300">
            📎
            <input
              type="file"
              accept="image/*"
              onChange={handleImageSelect}
              className="hidden"
              disabled={uploading}
            />
          </label>

          <textarea
            value={inputMessage}
            onChange={(e) => setInputMessage(e.target.value)}
            onKeyPress={handleKeyPress}
            placeholder="Type your message..."
            className="flex-1 p-2 border rounded resize-none"
            rows={2}
            disabled={uploading}
          />

          <button
            onClick={sendMessage}
            disabled={uploading || !connected || (!inputMessage.trim() && !selectedImage)}
            className="px-6 py-2 bg-blue-500 text-white rounded hover:bg-blue-600 disabled:opacity-50"
          >
            {uploading ? 'Uploading...' : 'Send'}
          </button>
        </div>
      </div>
    </div>
  );
};

export default WebSocketChat;
```

---

## 📦 Solution 2: Base64 Approach (Alternative)

### When to Use

- Small images only (< 1MB)
- Prototyping
- No HTTP endpoint available

### React Example

```jsx
const sendMessageWithBase64Image = async () => {
  let base64Image = null;

  if (selectedImage) {
    // Convert to base64
    const reader = new FileReader();
    base64Image = await new Promise((resolve) => {
      reader.onload = () => resolve(reader.result);
      reader.readAsDataURL(selectedImage);
    });
  }

  const wsMessage = {
    type: 'ai_request',
    data: {
      message: inputMessage,
      image_data: base64Image, // Base64 string
      provider: 'gemini',
    },
  };

  wsRef.current.send(JSON.stringify(wsMessage));
};
```

**⚠️ Warning:** Base64 adds ~33% size overhead and is not recommended for images > 1MB.

---

## 🔄 Flow Comparison

### Hybrid Approach (Recommended)

```
User → Select Image
     → HTTP POST /api/ai/upload-image/ (with file)
     → Backend saves to MinIO
     → Returns: {"image_url": "http://minio:9000/..."}
     → WebSocket: {"type": "ai_request", "data": {"image_url": "..."}}
     → Backend processes with AI
```

**Pros:**
- ✅ Efficient (no base64 overhead)
- ✅ Works with large images (up to 50MB)
- ✅ Image reusable (stored in MinIO)
- ✅ Better progress tracking
- ✅ Industry standard approach

### Base64 Approach

```
User → Select Image
     → Convert to Base64 (client-side)
     → WebSocket: {"type": "ai_request", "data": {"image_data": "data:image/..."}}
     → Backend decodes and processes
```

**Pros:**
- ✅ Simple (one request)
- ✅ No extra HTTP endpoint needed

**Cons:**
- ❌ 33% size increase
- ❌ Slow for large images
- ❌ Increases WebSocket message size
- ❌ No progress tracking

---

## 🎯 Recommendation

**Use the Hybrid Approach:**
1. Upload image via HTTP to `/api/ai/upload-image/`
2. Get MinIO URL back
3. Send URL via WebSocket

This is what production apps (Slack, Discord, WhatsApp) do because:
- More efficient
- Better UX (upload progress)
- Handles large files
- Cleaner architecture

---

## 📝 Quick Start

1. **Backend:** Create upload endpoint (see above)
2. **Frontend:** Use the WebSocketChat component
3. **Test:**
   - Select image
   - Image uploads to MinIO
   - MinIO URL sent via WebSocket
   - AI processes with image context

**Your MinIO setup is ready - it will save images to `jarvis-media/chat_images/`!** 🚀

