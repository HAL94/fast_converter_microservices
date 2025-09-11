import asyncio
from dataclasses import dataclass
import tempfile

from sqlalchemy import URL

from shared.constants import RECEIVER_CONFIGS, ExchangeNames
from shared.file_database.models import FileType
from shared.rabbitmq.client import RabbitmqClient
from shared.rabbitmq.receiver import RabbitmqExchangeReceiver
from shared.rabbitmq import IncomingMessage
from shared.database import SessionManager, Base
from shared.file_database.entities import File
from shared.minio_client import MinioClient, create_config, create_client
from .config import settings
from moviepy import VideoFileClip


@dataclass
class AudioConvertResult:
    audio_name: str | None
    success: bool


DATABASE_URL = URL.create(
    drivername="postgresql+asyncpg",
    username=settings.FILE_PG_USER,
    password=settings.FILE_PG_PW,
    host=settings.FILE_PG_HOST,
    port=settings.FILE_PG_PORT,
    database=settings.FILE_PG_DB,
)

session_manager = SessionManager(DATABASE_URL)


def setup_minio_client():
    minio_config = create_config(
        settings.MINIO_HOST, settings.MINIO_ROOT_USER, settings.MINIO_ROOT_PASSWORD
    )
    client = create_client(minio_config)
    if client.ensure_connect():
        print("[Video_to_mp3]: Minio client created")
    return client


client: MinioClient


async def connect_database():
    async with session_manager.engine.begin() as con:
        await con.run_sync(Base.metadata.create_all)


async def get_video_by_uuid(uuid: str) -> str | None:
    async with session_manager.session() as session:
        found = await File.get_one(session, uuid, field=File.model.uuid)
        if not found:
            print(f"Passed uuid: {uuid} is not found")
            return None
        print(f"Found video name: {found.name}")
        convert_result = convert_video_to_audio(found.name)
        if convert_result.success:
            await File.create(
                session,
                File(
                    name=convert_result.audio_name,
                    user_id=found.user_id,
                    original_file_id=found.id,
                    file_type=FileType.AUDIO,
                ),
            )
        return found.name


def convert_video_to_audio(filename: str):
    audio_ext = "mp3"
    retrieved_file = client.client.get_object(
        bucket_name="videos", object_name=filename
    )

    if retrieved_file.status != 200:
        raise ValueError(f"Failed retrieving file: {filename}")

    filename_without_ext = filename.split(".")[0]
    tf = tempfile.NamedTemporaryFile()

    tf.write(retrieved_file.data)

    audio = VideoFileClip(tf.name).audio

    tf.close()

    tf_path = tempfile.gettempdir() + f"/{filename_without_ext}.{audio_ext}"

    audio.write_audiofile(tf_path)

    write_audio_result = client.fput_object(
        bucket_name="videos",
        object_name=f"{filename_without_ext}.{audio_ext}",
        file_path=tf_path,
    )

    if write_audio_result.etag:
        return AudioConvertResult(
            audio_name=f"{filename_without_ext}.{audio_ext}", success=True
        )

    return AudioConvertResult(audio_name=None, success=False)


async def connect_rabbit():
    try:
        url = f"amqp://{settings.RABBITMQ_HOST}:{settings.RABBITMQ_PORT}/"
        username = settings.RABBITMQ_USERNAME
        password = settings.RABBITMQ_PASSWORD
        await RabbitmqClient.connect(url, username, password)
    except Exception as e:
        print(f"Failed to connect to RabbitMQ: {e}")
        raise e


async def setup_basic_receiver():
    try:
        receiver_config = RECEIVER_CONFIGS.get(ExchangeNames.VIDEO_UPLOAD)
        basic_receiver = RabbitmqExchangeReceiver(config=receiver_config)
        await basic_receiver.init_receiver()

        async def callback(message: IncomingMessage):
            async with message.process() as process:
                uuid = process.body.decode("utf-8")
                print(f" [x]: Received message from Gateway: {uuid}")
                await get_video_by_uuid(uuid)

        await basic_receiver.consume(callback=callback)
    except Exception as e:
        print(f"Failed to process: {e}")
        raise e


async def main():
    try:
        global client
        client = setup_minio_client()
        await connect_database()
        await connect_rabbit()
        await setup_basic_receiver()
        print("Conversion Service is running")
        await asyncio.Future()
    finally:
        await RabbitmqClient.close()


if __name__ == "__main__":
    asyncio.run(main())
