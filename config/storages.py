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
    bucket_name = settings.MINIO_BUCKET_NAME if hasattr(settings, 'MINIO_BUCKET_NAME') else 'jarvis-media'
    custom_domain = settings.MINIO_CUSTOM_DOMAIN if hasattr(settings, 'MINIO_CUSTOM_DOMAIN') else None
    file_overwrite = False
    default_acl = 'public-read'
    querystring_auth = False
    # Don't override __init__ - let S3Boto3Storage use AWS_* settings from settings.py


class MinIOPrivateStorage(S3Boto3Storage):
    """
    Private storage backend for sensitive files
    Files are not publicly accessible
    """
    bucket_name = settings.MINIO_BUCKET_NAME if hasattr(settings, 'MINIO_BUCKET_NAME') else 'jarvis-media'
    custom_domain = False  # Don't use custom domain for private files
    file_overwrite = False
    default_acl = 'private'
    querystring_auth = True  # Require signed URLs for private files


class MinIOChatMediaStorage(S3Boto3Storage):
    """
    Storage backend for chat images and media files
    Organized by user and conversation for easy management
    """
    bucket_name = settings.MINIO_BUCKET_NAME if hasattr(settings, 'MINIO_BUCKET_NAME') else 'jarvis-media'
    custom_domain = settings.MINIO_CUSTOM_DOMAIN if hasattr(settings, 'MINIO_CUSTOM_DOMAIN') else None
    file_overwrite = False
    default_acl = 'public-read'
    querystring_auth = False