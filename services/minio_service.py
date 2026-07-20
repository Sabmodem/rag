import logging
from pathlib import Path
import boto3
from botocore.exceptions import ClientError
from config import settings

logger = logging.getLogger(__name__)


class MinioService:
    def __init__(self):
        self.bucket = settings.minio_bucket
        self.public_url = settings.minio_public_url.rstrip('/')
        self.client = boto3.client(
            's3',
            endpoint_url=settings.minio_endpoint,
            aws_access_key_id=settings.minio_access_key,
            aws_secret_access_key=settings.minio_secret_key,
            region_name='us-east-1'
        )

    def ensure_bucket_exists(self) -> None:
        """Проверяет существование бакета и создает его при необходимости."""
        try:
            self.client.head_bucket(Bucket=self.bucket)
        except ClientError:
            try:
                self.client.create_bucket(Bucket=self.bucket)
                logger.info(f"Бакет '{self.bucket}' успешно создан.")
            except Exception as e:
                logger.error(f"Не удалось создать бакет '{self.bucket}': {e}")

    def upload_image(self, local_path: Path, object_name: str) -> str:
        """Загружает файл в MinIO и возвращает публичный URL."""
        try:
            self.client.upload_file(
                Filename=str(local_path),
                Bucket=self.bucket,
                Key=object_name,
                ExtraArgs={'ContentType': 'image/png'}
            )
            return f"{self.public_url}/{object_name}"
        except Exception as e:
            logger.error(f"Ошибка загрузки в MinIO {object_name}: {e}")
            return ""