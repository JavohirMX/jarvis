"""
Management command to setup MinIO bucket and policies
"""
from django.core.management.base import BaseCommand
from django.conf import settings
import boto3
from botocore.exceptions import ClientError
import json


class Command(BaseCommand):
    help = 'Setup MinIO bucket and configure policies'

    def handle(self, *args, **options):
        if not settings.USE_MINIO:
            self.stdout.write(self.style.WARNING(
                '⚠ MinIO is not enabled. Set USE_MINIO=True in your .env file.'
            ))
            return

        self.stdout.write('Setting up MinIO...\n')
        self.stdout.write(f'Endpoint: {settings.MINIO_ENDPOINT}')
        self.stdout.write(f'Bucket: {settings.MINIO_BUCKET_NAME}\n')

        try:
            # Create S3 client
            s3_client = boto3.client(
                's3',
                endpoint_url=settings.MINIO_ENDPOINT,
                aws_access_key_id=settings.MINIO_ACCESS_KEY,
                aws_secret_access_key=settings.MINIO_SECRET_KEY,
                region_name=settings.MINIO_REGION,
                use_ssl=settings.MINIO_USE_SSL,
                verify=False
            )
            self.stdout.write(self.style.SUCCESS('✓ Connected to MinIO'))

            bucket_name = settings.MINIO_BUCKET_NAME

            # Check if bucket exists
            try:
                s3_client.head_bucket(Bucket=bucket_name)
                self.stdout.write(self.style.SUCCESS(f'✓ Bucket "{bucket_name}" already exists'))
            except ClientError as e:
                error_code = e.response.get('Error', {}).get('Code', '')
                
                if error_code == '404':
                    # Bucket doesn't exist, create it
                    self.stdout.write(f'Creating bucket "{bucket_name}"...')
                    s3_client.create_bucket(Bucket=bucket_name)
                    self.stdout.write(self.style.SUCCESS(f'✓ Created bucket "{bucket_name}"'))
                else:
                    raise e

            # Set bucket policy for public read access
            self.stdout.write('Setting bucket policy...')
            bucket_policy = {
                "Version": "2012-10-17",
                "Statement": [
                    {
                        "Effect": "Allow",
                        "Principal": {"AWS": "*"},
                        "Action": ["s3:GetObject"],
                        "Resource": [
                            f"arn:aws:s3:::{bucket_name}/avatars/*",
                            f"arn:aws:s3:::{bucket_name}/chat_images/*"
                        ]
                    }
                ]
            }

            s3_client.put_bucket_policy(
                Bucket=bucket_name,
                Policy=json.dumps(bucket_policy)
            )
            self.stdout.write(self.style.SUCCESS('✓ Set public read policy for avatars/ and chat_images/'))

            # Verify setup by listing buckets
            response = s3_client.list_buckets()
            buckets = [b['Name'] for b in response['Buckets']]
            self.stdout.write(f'\nAvailable buckets: {", ".join(buckets)}')

            # Test upload
            self.stdout.write('\nTesting file upload...')
            test_key = 'test/.setup_test.txt'
            s3_client.put_object(
                Bucket=bucket_name,
                Key=test_key,
                Body=b'MinIO setup test file',
                ContentType='text/plain'
            )
            self.stdout.write(self.style.SUCCESS(f'✓ Test file uploaded: {test_key}'))

            # Clean up test file
            s3_client.delete_object(Bucket=bucket_name, Key=test_key)
            self.stdout.write('✓ Test file deleted')

            self.stdout.write('\n' + '='*60)
            self.stdout.write(self.style.SUCCESS('✓ MinIO setup completed successfully!'))
            self.stdout.write('='*60)
            self.stdout.write('\nYou can now upload files to MinIO.')
            self.stdout.write(f'MinIO Console: {settings.MINIO_ENDPOINT.replace(":9000", ":9001")}')

        except Exception as e:
            self.stdout.write('\n' + '='*60)
            self.stdout.write(self.style.ERROR(f'✗ MinIO setup failed: {e}'))
            self.stdout.write('='*60)
            self.stdout.write('\nTroubleshooting:')
            self.stdout.write('1. Check if MinIO is running')
            self.stdout.write('2. Verify MINIO_ENDPOINT is correct')
            self.stdout.write('3. Verify MINIO_ACCESS_KEY and MINIO_SECRET_KEY')
            self.stdout.write('4. Check network connectivity to MinIO')

