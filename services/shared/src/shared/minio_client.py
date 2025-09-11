from dataclasses import dataclass
from typing import BinaryIO
from minio import Minio


@dataclass
class MinioConfig:
    host: str
    username: str
    password: str


class MinioClient:
    def __init__(self, host: str, username: str, password: str):
        self.config = MinioConfig(host=host, username=username, password=password)
        self.client = Minio(
            host,  # Replace with your MinIO server endpoint
            access_key=username,  # Replace with your access key
            secret_key=password,  # Replace with your secret key
            secure=False,  # Set to True for HTTPS
        )

    def ensure_connect(self):
        try:
            if not self.client:
                self.client = Minio(
                    self.config.host,  # Replace with your MinIO server endpoint
                    access_key=self.config.username,  # Replace with your access key
                    secret_key=self.config.password,  # Replace with your secret key
                    secure=False,  # Set to True for HTTPS
                )
            return True
        except Exception:
            return False

    def bucket_exists(self, bucket_name: str) -> bool:
        found = self.client.bucket_exists(bucket_name)
        if not found:
            self.client.make_bucket(bucket_name)
            print("Created bucket", bucket_name)
            return True
        else:
            print("Bucket", bucket_name, "already exists")
            return False

    def put_object(
        self, bucket_name: str, object_name: str, data: BinaryIO, length: int, **kwargs
    ):
        if not self.client:
            raise ValueError("Client not initialized")

        try:
            object_put_result = self.client.put_object(
                bucket_name=bucket_name,
                object_name=object_name,
                data=data,
                length=length,
                **kwargs,
            )

            return object_put_result
        except Exception as e:
            print(f"Failed to upload data: {e}")

    def fput_object(self, bucket_name: str, object_name: str, file_path: str, **kwargs):
        if not self.client:
            raise ValueError("Client not initialized")
        try:
            object_put_result = self.client.fput_object(
                bucket_name=bucket_name,
                object_name=object_name,
                file_path=file_path,
                **kwargs,
            )
            return object_put_result
        except Exception as e:
            print(f"Failed to upload data: {e}")

def create_config(host: str, username: str, password: str):
    return MinioConfig(host=host, username=username, password=password)

def create_client(config: MinioConfig):
    return MinioClient(config.host, config.username, config.password)


