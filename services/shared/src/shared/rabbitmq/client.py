import traceback
import aio_pika
from aio_pika.abc import AbstractConnection, AbstractChannel


class RabbitmqClient:
    connection: AbstractConnection | None = None
    channel: AbstractChannel | None = None
    is_connected: bool | None = None

    @classmethod
    async def connect(cls, url: str = "amqp://localhost:5672/", username: str = "guest", password: str = "guest"):
        try:
            if cls.is_connected:
                print("RabbitMQ Connection is already established")
                return
            cls.connection = await aio_pika.connect(url=url, login=username, password=password)
            cls.channel = await cls.connection.channel()
            cls.is_connected = True
            print("Successfully connected to RabbitMQ")
        except aio_pika.exceptions.AMQPConnectionError as e:
            tb_str = traceback.format_exc()
            print(f"Failed to connect to RabbitMQ: {e}")
            print(tb_str)
            cls.connection = None
            cls.channel = None
            cls.is_connected = False

    @classmethod
    async def close(cls):
        if cls.is_connected:
            await cls.connection.close()
            print("RabbitMQ Connection is closed")
        else:
            print("RabbitMQ Connection is already closed")
