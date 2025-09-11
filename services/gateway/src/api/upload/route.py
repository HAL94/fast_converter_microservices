import io
from typing import Any

from shared.constants import PRODUCER_CONFIGS, ExchangeNames
from shared.rabbitmq.producer import RabbitmqExchangeProducer
from src.dependencies.database import get_filedb_async_session
from src.core.config import settings
from fastapi import APIRouter, Depends, HTTPException, UploadFile
from fastapi.params import File
from src.core.minio_client import client

from sqlalchemy.ext.asyncio import AsyncSession

from minio import S3Error
from src.dependencies.auth import validate_jwt
from shared.file_database.entities import File as FileModel
from shared.file_database.models import FileType

router = APIRouter(prefix="/upload")
BUCKET_NAME = "videos"


@router.post("/")
async def upload_file(
    video_file: UploadFile = File(None),
    session: AsyncSession = Depends(get_filedb_async_session),
    user_data: dict[str, Any] = Depends(validate_jwt),
):
    try:
        user_id = user_data.get("user_id")
        if not user_id:
            raise ValueError("Could not determine user")

        video_content = await video_file.read()
        video_bytes = io.BytesIO(video_content)
        video_size = len(video_content)

        object_put_result = client.put_object(
            bucket_name=BUCKET_NAME,
            object_name=video_file.filename,
            data=video_bytes,
            length=video_size,
            content_type=video_file.content_type,
        )
        print(f"ObjectPutResult: {object_put_result.etag}")

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

        config = PRODUCER_CONFIGS.get(ExchangeNames.VIDEO_UPLOAD)
        producer = RabbitmqExchangeProducer(exchange_config=config)
        await producer.init_producer()
        await producer.publish(body=file_record_result.uuid, routing_key="upload_file")

        return {
            "filename": video_file.filename,
            "message": "File uploaded successfully to MinIO",
            "location": f"http://{settings.MINIO_HOST}/{BUCKET_NAME}/{video_file.filename}",
            "details": file_record_result,
        }
    except S3Error as e:
        print(f"S3Error uploading: {e}")
        raise HTTPException(status_code=500, detail="Failed to upload") from e
    except Exception as e:
        print(f"Unknown error uploading: {e}")
        raise HTTPException(status_code=500, detail="Unknown error occured while uploading") from e
