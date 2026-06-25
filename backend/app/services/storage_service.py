import io
import structlog
from minio import Minio
from minio.error import S3Error

from app.core.config import settings

log = structlog.get_logger()


class StorageService:
    @staticmethod
    def _client() -> Minio:
        return Minio(
            settings.MINIO_ENDPOINT,
            access_key=settings.MINIO_ROOT_USER,
            secret_key=settings.MINIO_ROOT_PASSWORD,
            secure=settings.MINIO_SECURE,
        )

    @staticmethod
    def ensure_bucket():
        client = StorageService._client()
        try:
            if not client.bucket_exists(settings.MINIO_BUCKET):
                client.make_bucket(settings.MINIO_BUCKET)
                log.info("minio.bucket_created", bucket=settings.MINIO_BUCKET)
        except S3Error as e:
            log.error("minio.bucket_error", error=str(e))

    @staticmethod
    def upload_file(object_name: str, data: bytes, content_type: str = "application/octet-stream") -> str:
        client = StorageService._client()
        StorageService.ensure_bucket()
        client.put_object(
            settings.MINIO_BUCKET,
            object_name,
            io.BytesIO(data),
            length=len(data),
            content_type=content_type,
        )
        return f"{settings.MINIO_BUCKET}/{object_name}"

    @staticmethod
    def download_file(object_name: str) -> bytes:
        client = StorageService._client()
        response = client.get_object(settings.MINIO_BUCKET, object_name)
        return response.read()

    @staticmethod
    def delete_file(object_name: str):
        client = StorageService._client()
        client.remove_object(settings.MINIO_BUCKET, object_name)

    @staticmethod
    def list_files(prefix: str = "") -> list[str]:
        client = StorageService._client()
        objects = client.list_objects(settings.MINIO_BUCKET, prefix=prefix, recursive=True)
        return [obj.object_name for obj in objects]
