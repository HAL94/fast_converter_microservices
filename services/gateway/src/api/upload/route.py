import io
from typing import Any

from shared.constants import Buckets, ProducerConfigs, BindingKeys
from shared.rabbitmq.helpers import create_exchange_producer
from src.dependencies.database import get_filedb_async_session
from src.core.config import settings
from fastapi import APIRouter, Depends, HTTPException, UploadFile
from fastapi.params import File
from src.core.minio_client import client

from sqlalchemy.ext.asyncio import AsyncSession

from minio import S3Error
from src.dependencies.auth import ValidateJwt
from shared.file_database.entities import File as FileModel
from shared.file_database.models import FileType

router = APIRouter(prefix="/upload")


@router.get("/")
async def get_files(
    session: AsyncSession = Depends(get_filedb_async_session),
    user_data: dict[str, Any] = Depends(ValidateJwt()),
):
    try:
        user_id = user_data.get("user_id")
        return await FileModel.get_all(
            session, where_clause=[FileModel.model.user_id == user_id]
        )
    except Exception as e:
        print(f"Error occured: {e}")
        raise HTTPException(status_code=500, detail="Something went wrong") from e


@router.post("/")
async def upload_file(
    video_file: UploadFile = File(None),
    session: AsyncSession = Depends(get_filedb_async_session),
    user_data: dict[str, Any] = Depends(ValidateJwt()),
):
    try:
        user_id = user_data.get("user_id")
        video_content = await video_file.read()
        video_bytes = io.BytesIO(video_content)
        video_size = len(video_content)

        object_put_result = client.put_object(
            bucket_name=Buckets.VIDEO_BUCKET,
            object_name=video_file.filename,
            data=video_bytes,
            length=video_size,
            content_type=video_file.content_type,
        )

        if not object_put_result:
            raise ValueError("Failed to upload file")

        file_record_result: FileModel = await FileModel.get_one(
            session, video_file.filename, field=FileModel.model.name
        )
        if not file_record_result:
            data = FileModel(
                name=video_file.filename, file_type=FileType.VIDEO, user_id=user_id
            )
            file_record_result = await FileModel.create(session, data)

        producer = await create_exchange_producer(ProducerConfigs.VideoUpload)
        await producer.publish(
            body=file_record_result.uuid, routing_key=BindingKeys.UPLOAD_FILE
        )

        return {
            "filename": video_file.filename,
            "message": "File uploaded successfully to MinIO",
            "location": f"http://{settings.MINIO_HOST}/{Buckets.VIDEO_BUCKET}/{video_file.filename}",
            "details": file_record_result,
        }
    except S3Error as e:
        print(f"S3Error uploading: {e}")
        raise HTTPException(status_code=500, detail="Failed to upload") from e
    except Exception as e:
        print(f"Unknown error uploading: {e}")
        raise HTTPException(
            status_code=500, detail="Unknown error occured while uploading"
        ) from e
