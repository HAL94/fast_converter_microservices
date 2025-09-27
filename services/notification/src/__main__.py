import asyncio
from dataclasses import dataclass
from datetime import datetime, timedelta
import logging
import resend
from sqlalchemy import URL

from shared.constants import Buckets, ReceiverConfigs
from shared.database.session import SessionManager, create_session_manager
from shared.rabbitmq.client import RabbitmqClient
from shared.rabbitmq import IncomingMessage
from shared.rabbitmq.helpers import RabbitmqConnectionConfig, create_exchange_receiver
from shared.rabbitmq.receiver import RabbitmqExchangeReceiver
from shared.minio_client import (
    MinioClient,
    MinioConnectionConfig,
    create_client,
    create_config,
)
from shared.database.base import Base
from shared.file_database.entities import (
    File,
    FileModel,
    DownloadLink,
    DownloadLinkModel,
)
from shared.rabbitmq.types import ExchangeReceiverConfig
from .config import settings

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class NotificationConfig:
    minio_config: MinioConnectionConfig
    rabbitmq_config: RabbitmqConnectionConfig
    database_url: URL


class NotificationService:
    def __init__(self, config: NotificationConfig):
        self.config = config
        self.session_manager: SessionManager | None = None
        self.client: MinioClient | None = None
        self.receiver: RabbitmqExchangeReceiver | None = None
        self.service_initialized = False

    def _init_minio_client(self):
        try:
            client = create_client(self.config.minio_config)
            if client.ensure_connect():
                logger.info("[Notification Service]: Minio Client is created")
            return client
        except Exception as e:
            logger.error(f"[Notification Service]: Failed to setup minio client {e}")
            raise e

    async def _init_rabbitmq(self):
        try:
            config = self.config.rabbitmq_config

            url = f"amqp://{config.host}:{config.port}/"
            username = config.username
            password = config.password
            await RabbitmqClient.connect(url, username=username, password=password)
        except Exception as e:
            logger.error(
                f"[Notification Service] Failed to initialize RabbitMQ Connection: {e}"
            )
            raise e

    async def init_service(self):
        try:
            self.session_manager = create_session_manager(self.config.database_url)
            self.client = self._init_minio_client()
            await self._init_rabbitmq()
            async with self.session_manager.engine.begin() as con:
                await con.run_sync(Base.metadata.create_all)
            self.service_initialized = True
        except Exception as e:
            logger.error(f"[VideoToMp3 Service] failed to initialize: {e}")
            self.service_initialized = False
            raise e

    async def notify_user(self, uuid: str):
        expires_after = timedelta(hours=1)

        async with self.session_manager.session() as session:
            audio_file: FileModel = await File.get_one(
                session, uuid, field=File.model.uuid, return_as_base=True
            )
            if not audio_file:
                raise ValueError("Audio file is not found.. canceling")
                return

            url = self.client.get_presigned_url(
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

    async def start_consuming(self, config: ExchangeReceiverConfig):
        try:
            async def callback(message: IncomingMessage):
                async with message.process() as process:
                    uuid = process.body.decode()
                    logger.info(
                        f" [Notification Service]: [x] Received message: {uuid}"
                    )
                    await self.notify_user(uuid)

            self.receiver = await create_exchange_receiver(config=config)            
            await self.receiver.consume(callback=callback)
        except Exception as e:
            logger.error(
                f"[Notification Service]: Failed to setup rabbitmq consumer: {e}"
            )
            raise e

async def main():
    try:
        DATABASE_URL = URL.create(
            drivername="postgresql+asyncpg",
            username=settings.FILE_PG_USER,
            password=settings.FILE_PG_PW,
            host=settings.FILE_PG_HOST,
            port=settings.FILE_PG_PORT,
            database=settings.FILE_PG_DB,
        )
        minio_config = create_config(
            settings.MINIO_HOST, settings.MINIO_ROOT_USER, settings.MINIO_ROOT_PASSWORD
        )
        rabbitmq_config = RabbitmqConnectionConfig(
            host=settings.RABBITMQ_HOST,
            port=settings.RABBITMQ_PORT,
            username=settings.RABBITMQ_USERNAME,
            password=settings.RABBITMQ_PASSWORD,
        )
        service_config = NotificationConfig(
            database_url=DATABASE_URL,
            minio_config=minio_config,
            rabbitmq_config=rabbitmq_config,
        )
        service = NotificationService(config=service_config)
        await service.init_service()
        await service.start_consuming(ReceiverConfigs.ConvertCompleted)
        logger.info("[Notification Service]: is running...")
        await asyncio.Future()
    finally:
        await RabbitmqClient.close()


if __name__ == "__main__":
    asyncio.run(main())
