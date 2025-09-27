import asyncio
from dataclasses import dataclass
import logging
import tempfile

from pydantic import BaseModel
from sqlalchemy import URL

from shared.constants import Buckets, ProducerConfigs, ReceiverConfigs
from shared.file_database.models import FileType
from shared.rabbitmq.client import RabbitmqClient
from shared.rabbitmq.helpers import (
    RabbitmqConnectionConfig,
    create_exchange_producer,
    create_exchange_receiver,
)
from shared.rabbitmq import IncomingMessage
from shared.database import Base
from shared.database.session import SessionManager, create_session_manager
from shared.file_database.models import *  # noqa: F403
from shared.file_database.entities import File
from shared.minio_client import (
    MinioClient,
    MinioConnectionConfig,
    create_config,
    create_client,
)
from shared.rabbitmq.producer import RabbitmqExchangeProducer
from shared.rabbitmq.receiver import RabbitmqExchangeReceiver
from shared.rabbitmq.types import ExchangeProducerConfig, ExchangeReceiverConfig
from .config import settings
from moviepy import VideoFileClip

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class AudioConvertResult(BaseModel):
    audio_name: str | None
    success: bool


@dataclass
class VideoToMp3Config:
    database_url: URL
    minio_config: MinioConnectionConfig
    rabbitmq_config: RabbitmqConnectionConfig


class VideoToMp3Service:
    def __init__(self, config: VideoToMp3Config):
        self.config = config
        self.session_manager: SessionManager | None = None
        self.client: MinioClient | None = None
        self.receiver: RabbitmqExchangeReceiver | None = None
        self.producer: RabbitmqExchangeProducer | None = None
        self.service_initialized = False

    def _init_minio_client(self):
        try:
            client = create_client(self.config.minio_config)
            if client.ensure_connect():
                logger.info("[VideoToMp3 Service]: Minio client created")
            return client
        except Exception as e:
            logger.error(f"[VideoToMp3 Service]: Failed to setup minio client {e}")
            raise e

    async def get_video_by_uuid(self, uuid: str) -> str | None:
        async with self.session_manager.session() as session:
            found = await File.get_one(session, uuid, field=File.model.uuid)
            if not found:
                logger.info(f"[VideoToMp3 Service]: Passed uuid: {uuid} is not found")
                return None
            logger.info(f"[VideoToMp3 Service]: Found video name: {found.name}")
            convert_result = self.convert_video_to_audio(found.name)
            if convert_result.success:
                audio_found = await File.get_one(
                    session, convert_result.audio_name, field=File.model.name
                )
                logger.info(f"[VideoToMp3 Service]: Audio already exist: {audio_found}")
                if not audio_found:
                    audio_found = await File.create(
                        session,
                        File(
                            name=convert_result.audio_name,
                            user_id=found.user_id,
                            original_file_id=found.id,
                            file_type=FileType.AUDIO,
                        ),
                    )
                confirmation = await self.producer.publish(body=audio_found.uuid)
                if confirmation.delivery_tag:
                    logger.info(
                        "[VideoToMp3 Service]: Successfully converted to audio and published a conversion complete event"
                    )

            return found.name

    def convert_video_to_audio(self, filename: str):
        audio_ext = "mp3"
        retrieved_file = self.client.get_object(
            bucket_name="videos", object_name=filename
        )

        if not retrieved_file or retrieved_file.status != 200:
            raise ValueError(f"Failed retrieving file: {filename}")

        filename_without_ext = filename.split(".")[0]
        tf = tempfile.NamedTemporaryFile()

        tf.write(retrieved_file.data)

        audio = VideoFileClip(tf.name).audio

        tf.close()

        tf_path = tempfile.gettempdir() + f"/{filename_without_ext}.{audio_ext}"

        audio.write_audiofile(tf_path)

        write_audio_result = self.client.fput_object(
            bucket_name=Buckets.VIDEO_BUCKET,
            object_name=f"{filename_without_ext}.{audio_ext}",
            file_path=tf_path,
        )

        if write_audio_result.etag:
            return AudioConvertResult(
                audio_name=f"{filename_without_ext}.{audio_ext}", success=True
            )

        return AudioConvertResult(audio_name=None, success=False)

    async def _init_rabbitmq(self):
        try:
            config = self.config.rabbitmq_config

            url = f"amqp://{config.host}:{config.port}/"
            username = config.username
            password = config.password
            await RabbitmqClient.connect(url, username=username, password=password)
        except Exception as e:
            logger.error(
                f"[VideoToMP3 Service] Failed to initialize RabbitMQ Connection: {e}"
            )
            raise e

    async def init_service(self):
        try:
            self.session_manager = create_session_manager(self.config.database_url)
            self.client = self._init_minio_client()
            await self._init_rabbitmq()
            await self._start_exchange_producer(config=ProducerConfigs.ConvertCompleted)
            async with self.session_manager.engine.begin() as con:
                await con.run_sync(Base.metadata.create_all)

            self.service_initialized = True
        except Exception as e:
            logger.error(f"[VideoToMp3 Service] failed to initialize: {e}")
            self.service_initialized = False
            raise e

    async def _start_exchange_producer(self, config: ExchangeProducerConfig):
        try:
            self.producer = await create_exchange_producer(config=config)
            return self.producer
        except Exception as e:
            logger.error(
                f"[VideoToMp3 Service]: Failed to initialize Exchange Producer: {e}"
            )
            raise e

    async def start_consuming(
        self,
        config: ExchangeReceiverConfig,
    ):
        try:

            async def callback(message: IncomingMessage):
                async with message.process() as process:
                    uuid = process.body.decode("utf-8")
                    logger.info(f" [x]: Received message from Gateway: {uuid}")
                    await self.get_video_by_uuid(uuid)

            self.receiver = await create_exchange_receiver(config=config)
            await self.receiver.consume(callback=callback)

            return self.receiver
        except Exception as e:
            logger.error(f"[VideoToMp3 Service]: Failed to setup message consumer: {e}")
            raise e


DATABASE_URL = URL.create(
    drivername="postgresql+asyncpg",
    username=settings.FILE_PG_USER,
    password=settings.FILE_PG_PW,
    host=settings.FILE_PG_HOST,
    port=settings.FILE_PG_PORT,
    database=settings.FILE_PG_DB,
)


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
        service_config = VideoToMp3Config(
            database_url=DATABASE_URL,
            minio_config=minio_config,
            rabbitmq_config=rabbitmq_config,
        )

        service = VideoToMp3Service(config=service_config)
        await service.init_service()

        await service.start_consuming(config=ReceiverConfigs.VideoUpload)
        logger.info("[VideoToMP3 Service]: is running...")
        await asyncio.Future()
    finally:
        await RabbitmqClient.close()


if __name__ == "__main__":
    asyncio.run(main())
