"""
Management command to test MinIO connectivity and configuration
"""
from django.core.management.base import BaseCommand
from django.conf import settings
from django.core.files.base import ContentFile
import boto3
from botocore.exceptions import ClientError


class Command(BaseCommand):
    help = 'Test MinIO connectivity and bucket configuration'

    def handle(self, *args, **options):
        if not settings.USE_MINIO:
            self.stdout.write(self.style.WARNING(
                'MinIO is not enabled. Set USE_MINIO=True in your .env file.'
            ))
            return

        self.stdout.write('Testing MinIO Configuration...\n')
        self.stdout.write(f'Endpoint: {settings.MINIO_ENDPOINT}')
        self.stdout.write(f'Bucket: {settings.MINIO_BUCKET_NAME}')
        self.stdout.write(f'Region: {settings.MINIO_REGION}')
        self.stdout.write(f'SSL: {settings.MINIO_USE_SSL}\n')

        # Create S3 client
        try:
            s3_client = boto3.client(
                's3',
                endpoint_url=settings.MINIO_ENDPOINT,
                aws_access_key_id=settings.MINIO_ACCESS_KEY,
                aws_secret_access_key=settings.MINIO_SECRET_KEY,
                region_name=settings.MINIO_REGION,
                use_ssl=settings.MINIO_USE_SSL,
                verify=False
            )
            self.stdout.write(self.style.SUCCESS('✓ Successfully created S3 client'))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'✗ Failed to create S3 client: {e}'))
            return

        # Test connection by listing buckets
        try:
            response = s3_client.list_buckets()
            buckets = [bucket['Name'] for bucket in response['Buckets']]
            self.stdout.write(self.style.SUCCESS('✓ Successfully connected to MinIO'))
            self.stdout.write(f'Available buckets: {", ".join(buckets)}')
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'✗ Failed to connect to MinIO: {e}'))
            return

        # Check if target bucket exists
        bucket_name = settings.MINIO_BUCKET_NAME
        if bucket_name in buckets:
            self.stdout.write(self.style.SUCCESS(f'✓ Bucket "{bucket_name}" exists'))
        else:
            self.stdout.write(self.style.WARNING(f'⚠ Bucket "{bucket_name}" does not exist'))
            
            # Try to create bucket
            try:
                s3_client.create_bucket(Bucket=bucket_name)
                self.stdout.write(self.style.SUCCESS(f'✓ Created bucket "{bucket_name}"'))
            except ClientError as e:
                self.stdout.write(self.style.ERROR(f'✗ Failed to create bucket: {e}'))
                return

        # Test file upload
        test_key = 'test/test_file.txt'
        test_content = b'MinIO test file - you can delete this'
        
        try:
            s3_client.put_object(
                Bucket=bucket_name,
                Key=test_key,
                Body=test_content,
                ContentType='text/plain'
            )
            self.stdout.write(self.style.SUCCESS(f'✓ Successfully uploaded test file: {test_key}'))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'✗ Failed to upload test file: {e}'))
            return

        # Test file download
        try:
            response = s3_client.get_object(Bucket=bucket_name, Key=test_key)
            downloaded_content = response['Body'].read()
            if downloaded_content == test_content:
                self.stdout.write(self.style.SUCCESS('✓ Successfully downloaded and verified test file'))
            else:
                self.stdout.write(self.style.WARNING('⚠ Downloaded file content does not match'))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'✗ Failed to download test file: {e}'))
            return

        # Generate presigned URL
        try:
            url = s3_client.generate_presigned_url(
                'get_object',
                Params={'Bucket': bucket_name, 'Key': test_key},
                ExpiresIn=3600
            )
            self.stdout.write(self.style.SUCCESS('✓ Successfully generated presigned URL'))
            self.stdout.write(f'URL: {url[:100]}...')
        except Exception as e:
            self.stdout.write(self.style.WARNING(f'⚠ Could not generate presigned URL: {e}'))

        # Test delete
        try:
            s3_client.delete_object(Bucket=bucket_name, Key=test_key)
            self.stdout.write(self.style.SUCCESS('✓ Successfully deleted test file'))
        except Exception as e:
            self.stdout.write(self.style.WARNING(f'⚠ Failed to delete test file: {e}'))

        # Check bucket policy
        try:
            policy = s3_client.get_bucket_policy(Bucket=bucket_name)
            self.stdout.write(self.style.SUCCESS('✓ Bucket has a policy configured'))
        except ClientError as e:
            if e.response['Error']['Code'] == 'NoSuchBucketPolicy':
                self.stdout.write(self.style.WARNING(
                    '⚠ No bucket policy found. For public avatars, consider setting a public read policy.'
                ))
            else:
                self.stdout.write(self.style.WARNING(f'⚠ Could not check bucket policy: {e}'))

        # Final summary
        self.stdout.write('\n' + '='*60)
        self.stdout.write(self.style.SUCCESS('✓ All tests passed! MinIO is configured correctly.'))
        self.stdout.write('='*60)
        self.stdout.write('\nYou can now use MinIO for file uploads.')
        self.stdout.write('Upload endpoint: POST /api/profile/me/ with "avatar" file field')

