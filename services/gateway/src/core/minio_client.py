from shared.minio_client import MinioClient, create_client, create_config
from src.core.config import settings


def create_s3_storage_client():
    minio_config = create_config(
        settings.MINIO_HOST, settings.MINIO_ROOT_USER, settings.MINIO_ROOT_PASSWORD
    )
    client = create_client(minio_config)
    return client


client: MinioClient = create_s3_storage_client()
