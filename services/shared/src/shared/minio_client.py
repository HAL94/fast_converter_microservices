from datetime import timedelta
from typing import BinaryIO
from minio import Minio
from pydantic import BaseModel



class MinioConnectionConfig(BaseModel):
    host: str
    username: str
    password: str


class MinioClient:
    def __init__(self, host: str, username: str, password: str):
        self.config = MinioConnectionConfig(host=host, username=username, password=password)
        self.client = Minio(
            host,  # Replace with your MinIO server endpoint
            access_key=username,  # Replace with your access key
            secret_key=password,  # Replace with your secret key
            secure=False,  # Set to True for HTTPS
        )

    def get_presigned_url(self, bucket_name: str, file_name: str, expiration: timedelta):
        try:
            url = self.client.get_presigned_url(
                method="GET",
                bucket_name=bucket_name,
                object_name=file_name,
                expires=expiration,
                response_headers={
                    "Content-Disposition": f'attachment; filename="{file_name}"'
                },
            )
            return url
        except Exception as e:
            print(
                f"Failed to create pre-signed url for {bucket_name} and {file_name}: \n {e}"
            )
            raise e

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

    def get_object(self, bucket_name: str, object_name: str, **kwargs):
        if not self.client:
            raise ValueError("Client not initialized")
        try:
            return self.client.get_object(
                bucket_name=bucket_name, object_name=object_name, **kwargs
            )
        except Exception as e:
            print(f"Failed to upload data: {e}")
            return None

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
    return MinioConnectionConfig(host=host, username=username, password=password)


def create_client(config: MinioConnectionConfig):
    return MinioClient(config.host, config.username, config.password)
