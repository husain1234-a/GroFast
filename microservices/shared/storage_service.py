import boto3
import os
from typing import Optional
import asyncio
import aiofiles
from botocore.exceptions import ClientError

class R2StorageService:
    def __init__(self, endpoint_url: str, access_key: str, secret_key: str, bucket_name: str):
        self.bucket_name = bucket_name
        self.s3_client = boto3.client(
            's3',
            endpoint_url=endpoint_url,
            aws_access_key_id=access_key,
            aws_secret_access_key=secret_key,
            region_name='auto'
        )
    
    def upload_file(self, file_path: str, object_key: str) -> bool:
        """Upload file to R2 bucket"""
        try:
            self.s3_client.upload_file(file_path, self.bucket_name, object_key)
            return True
        except ClientError as e:
            print(f"Error uploading file: {e}")
            return False
    
    def generate_presigned_url(self, object_key: str, expiration: int = 3600) -> Optional[str]:
        """Generate presigned URL for private bucket access"""
        try:
            url = self.s3_client.generate_presigned_url(
                'get_object',
                Params={'Bucket': self.bucket_name, 'Key': object_key},
                ExpiresIn=expiration
            )
            return url
        except ClientError as e:
            print(f"Error generating presigned URL: {e}")
            return None
    
    def get_public_url(self, object_key: str, custom_domain: Optional[str] = None) -> str:
        """Get public URL for object (if bucket is public)"""
        if custom_domain:
            return f"https://{custom_domain}/{object_key}"
        else:
            return f"{self.s3_client._endpoint.host}/{self.bucket_name}/{object_key}"