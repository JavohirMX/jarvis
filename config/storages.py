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
    bucket_name = settings.MINIO_BUCKET_NAME
    custom_domain = settings.MINIO_CUSTOM_DOMAIN if hasattr(settings, 'MINIO_CUSTOM_DOMAIN') else None
    file_overwrite = False
    default_acl = 'public-read'
    
    def __init__(self, **settings_override):
        super().__init__(**settings_override)
        # Override with MinIO-specific settings
        self.access_key = settings.MINIO_ACCESS_KEY
        self.secret_key = settings.MINIO_SECRET_KEY
        self.endpoint_url = settings.MINIO_ENDPOINT
        self.region_name = getattr(settings, 'MINIO_REGION', 'us-east-1')


class MinIOPrivateStorage(S3Boto3Storage):
    """
    Private storage backend for sensitive files
    Files are not publicly accessible
    """
    bucket_name = settings.MINIO_BUCKET_NAME
    custom_domain = False  # Don't use custom domain for private files
    file_overwrite = False
    default_acl = 'private'
    
    def __init__(self, **settings_override):
        super().__init__(**settings_override)
        self.access_key = settings.MINIO_ACCESS_KEY
        self.secret_key = settings.MINIO_SECRET_KEY
        self.endpoint_url = settings.MINIO_ENDPOINT
        self.region_name = getattr(settings, 'MINIO_REGION', 'us-east-1')

