import logging
from fastapi import APIRouter, Depends, HTTPException, Response
from httpx import AsyncClient
from src.dependencies.database import get_filedb_async_session
from sqlalchemy.ext.asyncio import AsyncSession
from shared.file_database.entities import DownloadLink, DownloadLinkModel, File
import traceback

router = APIRouter(prefix="/download")

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@router.get("/audio/{uuid}")
async def get_audio(
    uuid: str, session: AsyncSession = Depends(get_filedb_async_session)
):
    file: File = await File.get_one(session, uuid, field=File.model.uuid)

    if not file:
        raise HTTPException(status_code=404, detail="File does not exist")

    download_link: DownloadLinkModel = await DownloadLink.get_one(
        session, file.id, field=DownloadLink.model.file_id, return_as_base=True
    )

    if not download_link:
        logger.info("[Gateway Service]: No download link for this file")
        raise HTTPException(status_code=404, detail="No download link for this file")
    if download_link.is_expired():
        
        logger.info(
            f"[Gateway Service]: Link has expired: {download_link.is_expired()}"
        )
        raise HTTPException(status_code=410, detail="Expired download link")
    if not download_link.is_valid():
        logger.info(f"[Gateway Service]: Link is not valid: {download_link.is_valid()}")
        raise HTTPException(status_code=410, detail="No longer active link")
    try:
        async with AsyncClient() as client:
            api_response = await client.get(download_link.presigned_url)

            if api_response.status_code == 200:
                download_link.accessed_count = download_link.accessed_count + 1
                await session.commit()

            api_response.headers.update({"Content-Type": "audio/mpeg"})

            return Response(
                content=api_response.content,
                status_code=api_response.status_code,
                headers=api_response.headers,
            )
    except Exception as e:
        print(f"Error has occured: {traceback.format_exc()}")
        raise HTTPException(status_code=410, detail="The resource has expired") from e
