# app/services/storage_service.py
import boto3
from botocore.exceptions import ClientError
from app.config import settings

class S3StorageService:
    def __init__(self):
        self.s3 = boto3.client(
            's3',
            aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
            aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
            region_name=settings.AWS_REGION
        )
        self.bucket = settings.AWS_BUCKET_NAME

    async def upload_file(self, file_data: bytes, filename: str) -> str:
        try:
            self.s3.put_object(
                Bucket=self.bucket,
                Key=f"profile_images/{filename}",
                Body=file_data,
                ContentType='image/jpeg'
            )
            return f"https://{self.bucket}.s3.amazonaws.com/profile_images/{filename}"
        except ClientError as e:
            raise Exception(f"S3 upload failed: {str(e)}")