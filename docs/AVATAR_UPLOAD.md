# Avatar Upload Guide

This guide shows how to upload and manage user profile avatars using the API.

## Overview

Users can upload profile pictures (avatars) that are stored either locally or in MinIO object storage. The avatar field is optional and supports common image formats (JPEG, PNG, GIF, WebP).

## Storage Options

### Local Storage (Default)
- Files stored in `media/avatars/` directory
- Accessible at `/media/avatars/filename.jpg`
- No additional setup required

### MinIO Object Storage
- Files stored in MinIO bucket
- Accessible via MinIO endpoint URL
- Better for production and scalability
- See [MINIO_SETUP.md](MINIO_SETUP.md) for configuration

## API Endpoints

### Upload Avatar

**Endpoint:** `PATCH /api/profile/me/`  
**Method:** PATCH  
**Content-Type:** multipart/form-data  
**Authentication:** Required (Bearer Token)

#### Request

```bash
curl -X PATCH http://localhost:8000/api/profile/me/ \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -F "avatar=@/path/to/your/image.jpg"
```

#### With Additional Profile Updates

```bash
curl -X PATCH http://localhost:8000/api/profile/me/ \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -F "avatar=@/path/to/your/image.jpg" \
  -F "theme=dark" \
  -F "notifications_enabled=true"
```

#### Response (Success)

```json
{
  "id": 1,
  "user": {
    "id": 1,
    "username": "johndoe",
    "email": "john@example.com"
  },
  "avatar": "http://localhost:9000/jarvis-media/avatars/user_1_avatar_abc123.jpg",
  "theme": "dark",
  "notifications_enabled": true,
  ...
}
```

### Get Profile with Avatar

**Endpoint:** `GET /api/profile/me/`  
**Method:** GET  
**Authentication:** Required (Bearer Token)

#### Request

```bash
curl -X GET http://localhost:8000/api/profile/me/ \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

#### Response

```json
{
  "id": 1,
  "user": {
    "id": 1,
    "username": "johndoe",
    "email": "john@example.com"
  },
  "avatar": "http://localhost:9000/jarvis-media/avatars/user_1_avatar_abc123.jpg",
  "theme": "dark",
  "ai_response_length": "medium",
  "notifications_enabled": true,
  "notification_sound": true,
  "notification_position": "bottom-right",
  "window_default_x": 100,
  "window_default_y": 100,
  "window_default_width": 400,
  "window_default_height": 600,
  "window_opacity": 0.95,
  "voice_enabled": true,
  "preferred_voice": "alloy",
  "voice_speed": 1.0,
  "voice_language": "en-US",
  "total_tokens_used": 1234,
  "current_month_tokens": 567,
  "current_day_tokens": 89,
  "daily_token_limit": 10000,
  "monthly_token_limit": 100000,
  "daily_remaining": 9911,
  "monthly_remaining": 99433,
  "is_premium_user": false,
  "created_at": "2024-01-15T10:30:00Z",
  "updated_at": "2024-01-20T15:45:00Z"
}
```

### Remove Avatar

To remove an avatar, send an empty string or null:

```bash
curl -X PATCH http://localhost:8000/api/profile/me/ \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"avatar": null}'
```

## Python Examples

### Using Requests Library

```python
import requests

# Login to get token
login_response = requests.post('http://localhost:8000/api/auth/login/', json={
    'username': 'johndoe',
    'password': 'securepassword'
})
token = login_response.json()['access']

# Upload avatar
with open('profile_picture.jpg', 'rb') as avatar_file:
    response = requests.patch(
        'http://localhost:8000/api/profile/me/',
        headers={'Authorization': f'Bearer {token}'},
        files={'avatar': avatar_file}
    )

print(response.json())
# Avatar URL: response.json()['avatar']
```

### Django Test Client

```python
from django.test import TestCase, Client
from django.contrib.auth.models import User
from django.core.files.uploadedfile import SimpleUploadedFile
from rest_framework_simplejwt.tokens import RefreshToken

class AvatarUploadTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        refresh = RefreshToken.for_user(self.user)
        self.token = str(refresh.access_token)
    
    def test_upload_avatar(self):
        # Create a test image
        image = SimpleUploadedFile(
            name='test_image.jpg',
            content=b'fake image content',
            content_type='image/jpeg'
        )
        
        response = self.client.patch(
            '/api/profile/me/',
            {'avatar': image},
            HTTP_AUTHORIZATION=f'Bearer {self.token}',
            format='multipart'
        )
        
        self.assertEqual(response.status_code, 200)
        self.assertIn('avatar', response.json())
        self.assertIsNotNone(response.json()['avatar'])
```

## JavaScript/TypeScript Examples

### Using Fetch API

```javascript
// Get auth token (from login)
const token = localStorage.getItem('access_token');

// Upload avatar
async function uploadAvatar(file) {
  const formData = new FormData();
  formData.append('avatar', file);
  
  const response = await fetch('http://localhost:8000/api/profile/me/', {
    method: 'PATCH',
    headers: {
      'Authorization': `Bearer ${token}`
    },
    body: formData
  });
  
  const data = await response.json();
  console.log('Avatar URL:', data.avatar);
  return data;
}

// Usage with file input
const fileInput = document.getElementById('avatarInput');
fileInput.addEventListener('change', async (e) => {
  const file = e.target.files[0];
  if (file) {
    await uploadAvatar(file);
  }
});
```

### Using Axios

```javascript
import axios from 'axios';

const api = axios.create({
  baseURL: 'http://localhost:8000/api',
  headers: {
    'Authorization': `Bearer ${localStorage.getItem('access_token')}`
  }
});

async function uploadAvatar(file) {
  const formData = new FormData();
  formData.append('avatar', file);
  
  try {
    const response = await api.patch('/profile/me/', formData, {
      headers: {
        'Content-Type': 'multipart/form-data'
      }
    });
    
    console.log('Avatar uploaded:', response.data.avatar);
    return response.data;
  } catch (error) {
    console.error('Upload failed:', error.response?.data);
    throw error;
  }
}
```

### React Component Example

```tsx
import React, { useState } from 'react';
import axios from 'axios';

const AvatarUpload: React.FC = () => {
  const [avatar, setAvatar] = useState<string | null>(null);
  const [uploading, setUploading] = useState(false);
  
  const handleFileChange = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;
    
    setUploading(true);
    
    const formData = new FormData();
    formData.append('avatar', file);
    
    try {
      const response = await axios.patch('/api/profile/me/', formData, {
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('access_token')}`,
          'Content-Type': 'multipart/form-data'
        }
      });
      
      setAvatar(response.data.avatar);
    } catch (error) {
      console.error('Upload failed:', error);
    } finally {
      setUploading(false);
    }
  };
  
  return (
    <div>
      {avatar && <img src={avatar} alt="Avatar" style={{ width: 100, height: 100, borderRadius: '50%' }} />}
      <input 
        type="file" 
        accept="image/*" 
        onChange={handleFileChange}
        disabled={uploading}
      />
      {uploading && <p>Uploading...</p>}
    </div>
  );
};

export default AvatarUpload;
```

## Image Requirements

### Supported Formats
- JPEG/JPG
- PNG
- GIF
- WebP

### Recommendations
- **Max file size**: 5MB (configurable in Django settings)
- **Recommended dimensions**: 512x512px or 1024x1024px
- **Aspect ratio**: Square (1:1) for best display
- **Format**: PNG or JPEG for best quality

### File Naming
Files are automatically renamed to prevent conflicts:
- Pattern: `avatars/user_{user_id}_avatar_{random_hash}.{ext}`
- Example: `avatars/user_1_avatar_abc123def456.jpg`

## Error Handling

### Common Errors

#### 400 Bad Request - Invalid File Type
```json
{
  "avatar": ["Upload a valid image. The file you uploaded was either not an image or a corrupted image."]
}
```

#### 413 Payload Too Large
```json
{
  "detail": "Request entity too large"
}
```

#### 401 Unauthorized
```json
{
  "detail": "Authentication credentials were not provided."
}
```

### Python Error Handling Example

```python
try:
    response = requests.patch(
        'http://localhost:8000/api/profile/me/',
        headers={'Authorization': f'Bearer {token}'},
        files={'avatar': avatar_file}
    )
    response.raise_for_status()
    avatar_url = response.json()['avatar']
except requests.exceptions.HTTPError as e:
    if e.response.status_code == 400:
        print("Invalid image file")
    elif e.response.status_code == 413:
        print("File too large")
    else:
        print(f"Error: {e.response.json()}")
```

## Security Considerations

1. **File Size Limit**: Enforced at Django level (default 5MB)
2. **File Type Validation**: Only image files accepted
3. **Authentication Required**: Must be authenticated to upload
4. **User Isolation**: Users can only upload their own avatar
5. **File Scanning**: Consider adding antivirus scanning in production

## Advanced Configuration

### Custom File Size Limit

In `settings.py`:
```python
# Max upload size: 10MB
DATA_UPLOAD_MAX_MEMORY_SIZE = 10 * 1024 * 1024
FILE_UPLOAD_MAX_MEMORY_SIZE = 10 * 1024 * 1024
```

### Custom Storage Path

In `profiles/models.py`:
```python
avatar = models.ImageField(
    upload_to='custom/path/avatars/',
    null=True,
    blank=True
)
```

### Image Processing (Optional)

Add image processing with Pillow:
```python
from PIL import Image
from io import BytesIO
from django.core.files.uploadedfile import InMemoryUploadedFile

def optimize_avatar(image_file, max_size=(512, 512)):
    """Resize and optimize avatar image"""
    img = Image.open(image_file)
    
    # Convert to RGB if necessary
    if img.mode != 'RGB':
        img = img.convert('RGB')
    
    # Resize
    img.thumbnail(max_size, Image.Resampling.LANCZOS)
    
    # Save to BytesIO
    output = BytesIO()
    img.save(output, format='JPEG', quality=85, optimize=True)
    output.seek(0)
    
    return InMemoryUploadedFile(
        output,
        'ImageField',
        f"{image_file.name.split('.')[0]}.jpg",
        'image/jpeg',
        output.tell(),
        None
    )
```

## Testing

### Test Avatar Upload

```bash
# Create a test image
convert -size 512x512 xc:blue test_avatar.jpg

# Upload
curl -X PATCH http://localhost:8000/api/profile/me/ \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -F "avatar=@test_avatar.jpg"
```

### Using Django Management Command

```bash
# Test MinIO connectivity
python manage.py test_minio
```

## Troubleshooting

### Avatar Not Displaying

1. Check if file was uploaded:
   ```bash
   curl -X GET http://localhost:8000/api/profile/me/ \
     -H "Authorization: Bearer YOUR_TOKEN"
   ```

2. Verify MinIO is running (if using MinIO):
   ```bash
   docker ps | grep minio
   ```

3. Check MinIO bucket exists:
   - Open http://localhost:9001
   - Login and verify bucket

### Permission Denied

1. Check file permissions on `media/` directory
2. Verify MinIO credentials in `.env`
3. Check bucket policy allows read access

## Related Documentation

- [MinIO Setup Guide](MINIO_SETUP.md)
- [API Documentation](API_DOCUMENTATION.md)
- [User Profile Management](USAGE_EXAMPLES.md)

