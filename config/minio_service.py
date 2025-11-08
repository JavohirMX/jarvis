"""
MinIO Service for file operations
Direct S3-compatible storage operations using boto3
Translated from NestJS implementation
"""
import os
import uuid
from typing import Optional, Tuple
from django.conf import settings
import boto3
from botocore.exceptions import ClientError


class MinioService:
    """Service for managing file uploads to MinIO"""
    
    def __init__(self):
        """Initialize S3 client with MinIO configuration"""
        endpoint = os.getenv('MINIO_ENDPOINT') or getattr(settings, 'MINIO_ENDPOINT', None)
        access_key = os.getenv('MINIO_ACCESS_KEY') or getattr(settings, 'MINIO_ACCESS_KEY', None)
        secret_key = os.getenv('MINIO_SECRET_KEY') or getattr(settings, 'MINIO_SECRET_KEY', None)
        
        if not endpoint or not access_key or not secret_key:
            raise ValueError(
                'MinIO configuration is missing in environment variables or settings'
            )
        
        self.endpoint = endpoint
        self.bucket_name = getattr(settings, 'MINIO_BUCKET_NAME', 'jarvis-media')
        self.use_ssl = getattr(settings, 'MINIO_USE_SSL', False)
        
        self.s3_client = boto3.client(
            's3',
            region_name='us-east-1',
            endpoint_url=endpoint,
            aws_access_key_id=access_key,
            aws_secret_access_key=secret_key,
            config=boto3.session.Config(
                signature_version='s3v4',
                s3={'addressing_style': 'path'}  # Force path style for MinIO
            ),
            use_ssl=self.use_ssl,
            verify=False  # Set to True in production with valid SSL
        )
    
    def upload_file(
        self,
        file_content: bytes,
        bucket_name: str,
        original_filename: str,
        content_type: str,
        custom_key: Optional[str] = None
    ) -> Tuple[str, str]:
        """
        Upload a file to MinIO bucket
        
        Args:
            file_content: Binary content of the file
            bucket_name: Name of the bucket
            original_filename: Original filename
            content_type: MIME type of the file
            custom_key: Optional custom key, generates UUID-based key if not provided
        
        Returns:
            Tuple of (url, key)
        """
        # Generate file key (similar to NestJS randomUUID() + filename)
        if custom_key:
            file_key = custom_key
        else:
            file_key = f"{uuid.uuid4()}-{original_filename}"
        
        # Upload to MinIO
        self.s3_client.put_object(
            Bucket=bucket_name,
            Key=file_key,
            Body=file_content,
            ContentType=content_type,
        )
        
        # Generate URL
        url = f"{self.endpoint}/{bucket_name}/{file_key}"
        
        return url, file_key
    
    def delete_file(self, bucket_name: str, file_key: str) -> bool:
        """
        Delete a file from MinIO bucket
        
        Args:
            bucket_name: Name of the bucket
            file_key: Key of the file to delete
        
        Returns:
            True if deletion succeeded, False if file not found
        
        Raises:
            Exception for other errors
        """
        try:
            # Check if object exists
            self.s3_client.head_object(
                Bucket=bucket_name,
                Key=file_key
            )
            
            # If exists, delete it
            self.s3_client.delete_object(
                Bucket=bucket_name,
                Key=file_key
            )
            
            return True  # Deletion succeeded
            
        except ClientError as err:
            error_code = err.response.get('Error', {}).get('Code', '')
            status_code = err.response.get('ResponseMetadata', {}).get('HTTPStatusCode', 0)
            
            # Object not found, nothing to delete
            if error_code == 'NotFound' or error_code == '404' or status_code == 404:
                return False
            
            # Other errors rethrown
            raise err
    
    def ensure_bucket_exists(self, bucket_name: str) -> None:
        """
        Ensure a bucket exists, create if it doesn't
        
        Args:
            bucket_name: Name of the bucket to check/create
        """
        try:
            self.s3_client.head_bucket(Bucket=bucket_name)
        except ClientError as err:
            error_code = err.response.get('Error', {}).get('Code', '')
            
            if error_code == '404' or error_code == 'NotFound':
                print(f"Bucket {bucket_name} does not exist, creating...")
                self.s3_client.create_bucket(Bucket=bucket_name)
                print(f"✓ Bucket {bucket_name} created successfully")
            else:
                raise err
    
    def file_exists(self, bucket_name: str, file_key: str) -> bool:
        """
        Check if a file exists in MinIO
        
        Args:
            bucket_name: Name of the bucket
            file_key: Key of the file to check
        
        Returns:
            True if file exists, False otherwise
        """
        try:
            self.s3_client.head_object(Bucket=bucket_name, Key=file_key)
            return True
        except ClientError:
            return False
    
    def list_files(self, bucket_name: str, prefix: str = '') -> list:
        """
        List files in a bucket with optional prefix
        
        Args:
            bucket_name: Name of the bucket
            prefix: Optional prefix to filter files
        
        Returns:
            List of file keys
        """
        try:
            response = self.s3_client.list_objects_v2(
                Bucket=bucket_name,
                Prefix=prefix
            )
            
            if 'Contents' not in response:
                return []
            
            return [obj['Key'] for obj in response['Contents']]
        except ClientError as err:
            print(f"Error listing files: {err}")
            return []


# Singleton instance
_minio_service = None


def get_minio_service() -> MinioService:
    """Get or create MinIO service singleton"""
    global _minio_service
    if _minio_service is None:
        _minio_service = MinioService()
    return _minio_service

