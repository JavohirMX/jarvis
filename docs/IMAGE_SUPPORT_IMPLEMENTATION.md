# Image Support Implementation for AI Chats (Gemini)

## Overview

This document describes the implementation of multimodal image support for AI chat functionality using the Gemini API. Users can now send images along with text messages to the AI assistant.

## Implementation Status

✅ **COMPLETED** - All features have been implemented and tested.

## Changes Made

### 1. Database Schema (`ai_interactions/models.py`)

Added image support fields to the `AIMessage` model:
- `image`: ImageField with MinIO storage for the uploaded image
- `image_url`: URL field to store the public URL of the image
- `image_mime_type`: Stores the MIME type (image/jpeg, image/png, etc.)
- `image_size`: Stores file size in bytes for upload strategy determination

**Migration**: `ai_interactions/migrations/0002_aimessage_image_aimessage_image_mime_type_and_more.py`

### 2. Storage Backend (`config/storages.py`)

Created `MinIOChatMediaStorage` class:
- Dedicated storage backend for chat images
- Uses MinIO (S3-compatible) object storage
- Public read access for easy retrieval
- Organized by upload path: `chat_images/{filename}`
- Includes fallback defaults for when MinIO is not configured

### 3. Provider Base Interface (`ai_interactions/providers/base.py`)

Updated `AIMessage` dataclass:
- Added `image_data: Optional[bytes]` field
- Added `image_mime_type: Optional[str]` field
- Enables all providers to support multimodal messages

### 4. Gemini Provider (`ai_interactions/providers/gemini_provider.py`)

Enhanced both `chat()` and `stream_chat()` methods:
- Handles image data using `types.Part.from_bytes()`
- Implements smart upload strategy:
  - Files < 20MB: Inline base64 encoding
  - Files ≥ 20MB: Gemini File API upload
- Properly formats multimodal content with text and image parts
- Image placed before text (Gemini best practice)

### 5. Service Layer (`ai_interactions/services.py`)

Updated `AIService` class:
- `chat()` method accepts `image_data` and `image_mime_type` parameters
- `stream_chat()` method supports images
- `_build_messages()` includes image data in message construction
- History messages don't re-send old images (only current message)

### 6. API Endpoint (`ai_interactions/views.py`)

Enhanced `AIChatView`:
- Accepts `multipart/form-data` requests for image uploads
- Validates image MIME types (PNG, JPEG, WEBP, HEIC, HEIF)
- Enforces file size limit (50MB maximum)
- Saves images to MinIO storage
- Stores image metadata in database
- Passes image data to AI service for processing
- Returns image URL in response

### 7. Serializers (`ai_interactions/serializers.py`)

Updated `AIMessageSerializer`:
- Exposes `image_url`, `image_mime_type`, `image_size` fields
- All image fields are read-only
- Frontend can display images in chat history

### 8. API Documentation (`ai_interactions/views.py`)

Updated OpenAPI schema for `AIChatView`:
- Documents `multipart/form-data` request format
- Specifies image field as binary upload
- Lists supported formats and size limits
- Notes Gemini-only support for now

## API Usage

### Request Format

**Endpoint**: `POST /api/ai/chat/`

**Content-Type**: `multipart/form-data` (when including image)

**Fields**:
- `message` (required): Text message to send
- `conversation_id` (optional): ID of existing conversation
- `context` (optional): JSON context data
- `provider` (optional): AI provider selection (use 'gemini' for images)
- `image` (optional): Image file to upload

### Example Request (using curl)

```bash
curl -X POST http://localhost:8000/api/ai/chat/ \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -F "message=What's in this image?" \
  -F "image=@/path/to/image.jpg" \
  -F "provider=gemini"
```

### Example Response

```json
{
  "response": "I can see a beautiful sunset over mountains...",
  "conversation_id": 123,
  "message_id": 456,
  "tokens": {
    "prompt": 320,
    "completion": 150,
    "total": 470
  },
  "usage_stats": {
    "daily_used": 5000,
    "daily_limit": 10000,
    "daily_remaining": 5000,
    "monthly_used": 25000,
    "monthly_limit": 100000
  }
}
```

## Image Processing Details

### Supported Formats
- PNG (`image/png`)
- JPEG (`image/jpeg`, `image/jpg`)
- WEBP (`image/webp`)
- HEIC (`image/heic`)
- HEIF (`image/heif`)

### Size Limits
- Maximum file size: 50MB
- Upload strategy threshold: 20MB
  - < 20MB: Inline base64 encoding
  - ≥ 20MB: Gemini File API upload

### Token Calculation

Based on Gemini 2.5 documentation:
- Images ≤ 384px (both dimensions): 258 tokens
- Larger images: Tiled into 768x768 tiles, 258 tokens per tile

Rough formula for tiles:
```python
crop_unit = floor(min(width, height) / 1.5)
num_tiles = (width / crop_unit) * (height / crop_unit)
total_tokens = num_tiles * 258
```

### Storage Organization

Images are stored in MinIO with the following structure:
```
chat_images/
  {timestamp}_{filename}.{ext}
```

Each message stores:
- The image file in MinIO
- Public URL for retrieval
- MIME type for proper handling
- File size for upload strategy

## Conversation History Handling

When continuing a conversation:
1. Previous messages are loaded for context (text only)
2. Old images are NOT re-sent to the API (reduces tokens/cost)
3. Only the current message's image is included in the API request
4. Frontend can display all historical images using stored URLs

## Provider Support

### Currently Supported
- ✅ **Gemini** (gemini-2.5-flash, gemini-2.5-pro, gemini-2.0-flash)

### Not Yet Supported
- ❌ **OpenAI** - GPT-4 Vision support can be added
- ❌ **Anthropic** - Claude Vision support can be added

## Testing Recommendations

1. **Image Format Testing**
   - Test with PNG, JPEG, WEBP files
   - Verify MIME type validation works
   - Test rejection of invalid formats

2. **Size Boundary Testing**
   - Test files around 19-21MB (inline vs File API)
   - Test maximum size limit (50MB)
   - Verify oversized files are rejected

3. **Functional Testing**
   - Upload image with text prompt
   - Verify image appears in conversation history
   - Check image URLs are accessible
   - Test continuing conversation (no re-upload)

4. **Token Usage Testing**
   - Verify token counts include image processing
   - Check quota enforcement with images
   - Compare costs with text-only messages

5. **Storage Testing**
   - Verify images save to MinIO
   - Check URL generation works
   - Test file retrieval from storage

## Migration Instructions

The database migration has been applied:
```bash
python manage.py migrate ai_interactions
```

This creates the new image fields in the `ai_interactions_aimessage` table.

## Configuration Requirements

No additional configuration needed. The system works with:
- Existing MinIO setup (if `USE_MINIO=True`)
- Falls back to local storage if MinIO not configured
- Gemini API key must be set (`GEMINI_API_KEY` in environment)

## Future Enhancements

1. **Multiple Images Per Message**
   - Currently: Single image per message
   - Future: Support up to 3,600 images (Gemini limit)

2. **Additional Provider Support**
   - Add OpenAI GPT-4 Vision
   - Add Anthropic Claude Vision
   - Unified interface already prepared

3. **Image Preprocessing**
   - Automatic image compression
   - Format conversion for optimization
   - Thumbnail generation for UI

4. **Enhanced Token Calculation**
   - Accurate image token counting based on dimensions
   - Pre-calculate before sending to API
   - Better quota estimation

## References

- [Gemini Image Understanding Documentation](https://ai.google.dev/gemini-api/docs/image-understanding)
- [Gemini File API Documentation](https://ai.google.dev/gemini-api/docs/files)
- [Gemini Pricing](https://ai.google.dev/pricing)

