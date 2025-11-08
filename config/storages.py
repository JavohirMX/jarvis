"""
Custom storage backends for MinIO object storage
"""
from django.conf import settings
from storages.backends.s3boto3 import S3Boto3Storage


class MinIOMediaStorage(S3Boto3Storage):
    """
    Custom storage backend for MinIO (S3-compatible) media files
    Used for user avatar uploads and other media
    """
    bucket_name = getattr(settings, 'MINIO_BUCKET_NAME', 'ai-assistant-media')
    custom_domain = getattr(settings, 'MINIO_CUSTOM_DOMAIN', None)
    file_overwrite = False
    default_acl = 'public-read'
    
    def __init__(self, **settings_override):
        super().__init__(**settings_override)
        # Override with MinIO-specific settings
        self.access_key = getattr(settings, 'MINIO_ACCESS_KEY', 'minioadmin')
        self.secret_key = getattr(settings, 'MINIO_SECRET_KEY', 'minioadmin')
        self.endpoint_url = getattr(settings, 'MINIO_ENDPOINT', 'http://localhost:9000')
        self.region_name = getattr(settings, 'MINIO_REGION', 'us-east-1')


class MinIOPrivateStorage(S3Boto3Storage):
    """
    Private storage backend for sensitive files
    Files are not publicly accessible
    """
    bucket_name = getattr(settings, 'MINIO_BUCKET_NAME', 'ai-assistant-media')
    custom_domain = False  # Don't use custom domain for private files
    file_overwrite = False
    default_acl = 'private'
    
    def __init__(self, **settings_override):
        super().__init__(**settings_override)
        self.access_key = getattr(settings, 'MINIO_ACCESS_KEY', 'minioadmin')
        self.secret_key = getattr(settings, 'MINIO_SECRET_KEY', 'minioadmin')
        self.endpoint_url = getattr(settings, 'MINIO_ENDPOINT', 'http://localhost:9000')
        self.region_name = getattr(settings, 'MINIO_REGION', 'us-east-1')


class MinIOChatMediaStorage(S3Boto3Storage):
    """
    Storage backend for chat images and media files
    Organized by user and conversation for easy management
    """
    bucket_name = getattr(settings, 'MINIO_BUCKET_NAME', 'ai-assistant-media')
    custom_domain = getattr(settings, 'MINIO_CUSTOM_DOMAIN', None)
    file_overwrite = False
    default_acl = 'public-read'
    
    def __init__(self, **settings_override):
        super().__init__(**settings_override)
        self.access_key = getattr(settings, 'MINIO_ACCESS_KEY', 'minioadmin')
        self.secret_key = getattr(settings, 'MINIO_SECRET_KEY', 'minioadmin')
        self.endpoint_url = getattr(settings, 'MINIO_ENDPOINT', 'http://localhost:9000')
        self.region_name = getattr(settings, 'MINIO_REGION', 'us-east-1')

