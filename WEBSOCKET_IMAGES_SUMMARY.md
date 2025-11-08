# WebSocket + Image Upload - Implementation Summary

## 🎯 Problem

Your chat uses WebSockets for real-time messaging, but WebSocket doesn't natively support file uploads like HTTP multipart/form-data does.

## ✅ Solution: Hybrid Approach (Industry Standard)

**How it works:**
1. Upload image via **HTTP** → Get MinIO URL
2. Send MinIO URL via **WebSocket** → AI processes with image context

This is what **Slack, Discord, and WhatsApp** do.

---

## 📝 Changes Made

### 1. **Backend: WebSocket Consumer** (`realtime/consumers.py`)

**Added image support to `handle_ai_request`:**

```python
async def handle_ai_request(self, data):
    message = data.get('data', {}).get('message', '').strip()
    conversation_id = data.get('data', {}).get('conversation_id')
    context = data.get('data', {}).get('context', {})
    provider = data.get('data', {}).get('provider')
    image_url = data.get('data', {}).get('image_url')  # ← NEW!
    
    # Save user message with image URL
    user_message = await self.save_user_message(conversation, message, context, image_url)
```

**Updated `save_user_message` to store image URL:**

```python
@database_sync_to_async
def save_user_message(self, conversation, message, context, image_url=None):
    msg = AIMessage.objects.create(...)
    
    if image_url:
        msg.image_url = image_url
        msg.save(update_fields=['image_url'])
    
    return msg
```

### 2. **Backend: HTTP Upload Endpoint** (`ai_interactions/views.py`)

**Created new view for image upload:**

```python
class UploadChatImageView(APIView):
    """
    Upload image for chat message
    Returns MinIO URL to be sent via WebSocket
    """
    permission_classes = (IsAuthenticated,)
    
    def post(self, request):
        image_file = request.FILES.get('image')
        
        # Validate (type, size)
        # Save to MinIO via default_storage
        # Return MinIO URL
        
        return Response({
            'image_url': image_url,
            'filename': saved_path,
            'size': image_file.size,
            'mime_type': image_file.content_type,
        })
```

### 3. **Backend: URL Route** (`ai_interactions/urls.py`)

```python
urlpatterns = [
    path('upload-image/', views.UploadChatImageView.as_view(), name='upload-chat-image'),
    # ... other routes
]
```

---

## 🚀 React Frontend Usage

### Complete WebSocket Chat Component

```jsx
const WebSocketChat = () => {
  const [selectedImage, setSelectedImage] = useState(null);
  const [uploading, setUploading] = useState(false);
  const wsRef = useRef(null);

  // 1. Upload image via HTTP
  const uploadImage = async () => {
    if (!selectedImage) return null;

    const formData = new FormData();
    formData.append('image', selectedImage);

    const response = await axios.post(
      'http://localhost:8000/api/ai/upload-image/',
      formData,
      {
        headers: {
          'Authorization': `Bearer ${TOKEN}`,
          'Content-Type': 'multipart/form-data',
        },
      }
    );

    return response.data.image_url; // MinIO URL
  };

  // 2. Send message via WebSocket with image URL
  const sendMessage = async () => {
    // Upload image first
    let imageUrl = null;
    if (selectedImage) {
      imageUrl = await uploadImage();
    }

    // Send via WebSocket
    const wsMessage = {
      type: 'ai_request',
      data: {
        message: inputMessage || 'What\'s in this image?',
        image_url: imageUrl, // ← MinIO URL
        provider: imageUrl ? 'gemini' : undefined,
      },
    };

    wsRef.current.send(JSON.stringify(wsMessage));
  };

  // ... rest of component
};
```

---

## 🔄 Complete Flow

```
┌─────────────┐
│   Browser   │
└──────┬──────┘
       │ 1. User selects image
       │
       ▼
┌─────────────────────────────────┐
│ HTTP POST /api/ai/upload-image/ │
│ (multipart/form-data)           │
└──────┬──────────────────────────┘
       │
       ▼
┌─────────────┐
│   Django    │ 2. Saves to MinIO
└──────┬──────┘
       │
       ▼
┌─────────────┐
│    MinIO    │ 3. Returns URL
└──────┬──────┘    http://minio:9000/jarvis-media/chat_images/...
       │
       ▼
┌─────────────┐
│   Browser   │ 4. Sends message via WebSocket
└──────┬──────┘    {"type": "ai_request", "data": {"image_url": "..."}}
       │
       ▼
┌─────────────┐
│  WebSocket  │ 5. Streams AI response
│  Consumer   │
└──────┬──────┘
       │
       ▼
┌─────────────┐
│  AI Service │ 6. Processes with image (Gemini)
│   (Gemini)  │
└──────┬──────┘
       │
       ▼
┌─────────────┐
│   Browser   │ 7. Displays AI response (streamed)
└─────────────┘
```

---

## 📊 API Endpoints

### Upload Image

```bash
POST /api/ai/upload-image/
Content-Type: multipart/form-data

{
  "image": <file>
}
```

**Response:**
```json
{
  "image_url": "http://212.85.26.109:9000/jarvis-media/chat_images/user_1/abc123.jpg",
  "filename": "chat_images/user_1/abc123.jpg",
  "size": 1234567,
  "mime_type": "image/jpeg"
}
```

### Send Message via WebSocket

```javascript
// WebSocket message format
{
  "type": "ai_request",
  "data": {
    "message": "What's in this image?",
    "image_url": "http://minio:9000/jarvis-media/chat_images/user_1/abc123.jpg",
    "provider": "gemini",
    "conversation_id": 123  // optional
  }
}
```

---

## 🎨 Features

✅ **Efficient**: No base64 overhead, direct file upload  
✅ **Large Files**: Supports up to 50MB images  
✅ **Progress**: HTTP upload shows progress  
✅ **MinIO Storage**: Images saved to `jarvis-media/chat_images/`  
✅ **Reusable**: Image URLs can be shared/reused  
✅ **Streaming**: AI responses still stream in real-time  
✅ **Validated**: File type and size validation  
✅ **Secure**: Requires authentication  

---

## 🧪 Testing

### Test Image Upload

```bash
curl -X POST http://localhost:8000/api/ai/upload-image/ \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -F "image=@test.jpg"
```

**Expected response:**
```json
{
  "image_url": "http://localhost:9000/jarvis-media/chat_images/user_1/abc123.jpg",
  "filename": "chat_images/user_1/abc123.jpg",
  "size": 123456,
  "mime_type": "image/jpeg"
}
```

### Test via WebSocket

```javascript
// In browser console
const ws = new WebSocket('ws://localhost:8000/ws/assistant/?token=YOUR_TOKEN');

ws.onopen = () => {
  ws.send(JSON.stringify({
    type: 'ai_request',
    data: {
      message: 'What is this?',
      image_url: 'http://localhost:9000/jarvis-media/chat_images/user_1/test.jpg',
      provider: 'gemini'
    }
  }));
};

ws.onmessage = (event) => {
  console.log('Response:', JSON.parse(event.data));
};
```

---

## 📁 Files Modified

1. **`realtime/consumers.py`** - Added image_url support
2. **`ai_interactions/views.py`** - Created UploadChatImageView
3. **`ai_interactions/urls.py`** - Added upload-image route
4. **`docs/WEBSOCKET_IMAGE_UPLOAD.md`** - Complete guide

---

## 🎯 Why This Approach?

### ✅ Pros

- **Standard Practice**: Used by Slack, Discord, WhatsApp
- **Efficient**: No base64 encoding overhead
- **Scalable**: Works with large images
- **Better UX**: Upload progress, separate from message sending
- **Flexible**: Image can be uploaded before or during typing
- **Cacheable**: MinIO URLs can be cached by CDN

### ❌ Base64 Alternative (Not Recommended)

- 33% size increase
- No progress tracking
- Bloats WebSocket messages
- Slower for large images
- Not standard practice

---

## 🚀 Next Steps

1. **Deploy**: Push changes to production
2. **Test**: Upload image and send via WebSocket
3. **Frontend**: Implement WebSocketChat component
4. **Monitor**: Check MinIO for uploaded images

---

## 📖 Documentation

- Full guide: `docs/WEBSOCKET_IMAGE_UPLOAD.md`
- React examples included
- Base64 alternative documented
- Production best practices

---

**Status:** ✅ Complete  
**Date:** November 8, 2025  
**Approach:** Hybrid (HTTP Upload + WebSocket Message)  
**Storage:** MinIO (`jarvis-media/chat_images/`)

