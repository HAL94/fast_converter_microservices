import asyncio
from datetime import datetime, timedelta
import logging
import resend

from shared.constants import Buckets, ReceiverConfigs
from shared.rabbitmq.client import RabbitmqClient
from shared.rabbitmq import IncomingMessage
from shared.rabbitmq.helpers import create_exchange_receiver
from shared.rabbitmq.receiver import RabbitmqExchangeReceiver
from shared.minio_client import MinioClient, create_client, create_config
from shared.database.base import Base
from shared.file_database.entities import (
    File,
    FileModel,
    DownloadLink,
    DownloadLinkModel,
)
from .config import settings
from .files_database import session_manager

receiver: RabbitmqExchangeReceiver | None = None
client: MinioClient | None = None

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def create_minio_client():
    global client
    config = create_config(
        host=settings.MINIO_HOST,
        username=settings.MINIO_ROOT_USER,
        password=settings.MINIO_ROOT_PASSWORD,
    )
    client = create_client(config=config)


async def connect_rabbitmq():
    url = f"amqp://{settings.RABBITMQ_HOST}:{settings.RABBITMQ_PORT}"
    username = settings.RABBITMQ_USERNAME
    password = settings.RABBITMQ_PASSWORD
    await RabbitmqClient.connect(url=url, username=username, password=password)


async def connect_files_db():
    async with session_manager.engine.begin() as con:
        await con.run_sync(Base.metadata.create_all)


async def notify_user(uuid: str):
    expires_after = timedelta(hours=1)

    async with session_manager.session() as session:
        audio_file: FileModel = await File.get_one(
            session, uuid, field=File.model.uuid, return_as_base=True
        )
        if not audio_file:
            raise ValueError("Audio file is not found.. canceling")
            return

        url = client.get_presigned_url(
            bucket_name=Buckets.VIDEO_BUCKET,
            file_name=audio_file.name,
            expiration=expires_after,
        )
        if not url:
            logger.info(f"Failed to create pre-signed url for {uuid}")
            return

        logger.info(f"Generated a presigned url for the file: {uuid}, url: {url}")

        download_link: DownloadLinkModel = await DownloadLink.get_one(
            session,
            audio_file.id,
            field=DownloadLink.model.file_id,
            return_as_base=True,
        )

        if not download_link:
            download_link = await DownloadLink.create(
                session,
                DownloadLink(
                    bucket_name=Buckets.VIDEO_BUCKET,
                    presigned_url=url,
                    expires_at=datetime.now() + expires_after,
                    file_id=audio_file.id,
                ),
                return_as_base=True,
            )
        else:
            logger.info(
                f"Download link object already exist for this file, updating info: {download_link}"
            )
            download_link.presigned_url = url
            download_link.expires_at = datetime.now() + expires_after
            await session.commit()

        resend.api_key = settings.EMAIL_SERVICE
        total_seconds = expires_after.total_seconds()
        hours = int(total_seconds // 3600)
        wrapper_link = f"{settings.GATEWAY_API_DOWNLOAD}/{audio_file.uuid}"
        resend.Emails.send(
            {
                "from": "onboarding@resend.dev",
                "to": settings.DEV_EMAIL,
                "subject": "Your file is converted and ready",
                "html": f"<p>Below is the link for your file, it will be valid for {hours} hour(s), {wrapper_link}!</p>",
            }
        )


async def setup_exchange_receiver():
    global receiver
    receiver = await create_exchange_receiver(ReceiverConfigs.ConvertCompleted)

    async def callback(message: IncomingMessage):
        async with message.process() as process:
            uuid = process.body.decode("utf-8")
            print(f" [x]: Received message: {uuid}")
            await notify_user(uuid)

    await receiver.consume(callback=callback)


async def main():
    try:
        await connect_rabbitmq()
        await setup_exchange_receiver()
        await connect_files_db()
        create_minio_client()
        print("Hello from notification!")
        await asyncio.Future()
    finally:
        await RabbitmqClient.close()


if __name__ == "__main__":
    asyncio.run(main())
