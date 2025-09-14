import asyncio

from shared.constants import Buckets, ReceiverConfigs
from shared.rabbitmq.client import RabbitmqClient
from shared.rabbitmq import IncomingMessage
from shared.rabbitmq.helpers import create_exchange_receiver
from shared.rabbitmq.receiver import RabbitmqExchangeReceiver
from shared.minio_client import MinioClient, create_client, create_config
from .config import settings

receiver: RabbitmqExchangeReceiver | None = None
client: MinioClient | None = None


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


async def notify_user(uuid: str):
    url = client.get_presigned_url(
        bucket_name=Buckets.VIDEO_BUCKET, file_name="siberian_husky.mp3"
    )
    print(f"Generated a presigned url for the file: {uuid}, url: {url}")


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
        create_minio_client()
        print("Hello from notification!")
        await asyncio.Future()
    finally:
        await RabbitmqClient.close()


if __name__ == "__main__":
    asyncio.run(main())
