import asyncio

from shared.constants import RECEIVER_CONFIGS, ExchangeNames
from shared.rabbitmq.client import RabbitmqClient
from shared.rabbitmq.receiver import RabbitmqExchangeReceiver
from shared.rabbitmq import IncomingMessage


async def connect_rabbit():
    try:
        url = "amqp://rabbitmq:5672"
        username = "rabbit"
        password = "rabbit"
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
                message_body = process.body.decode("utf-8")
                print(f" [x]: Received message from Gateway: {message_body}")

        await basic_receiver.consume(callback=callback)
    except Exception as e:
        print(f"Failed to process: {e}")
        raise e


async def main():
    try:
        await connect_rabbit()
        await setup_basic_receiver()
        print("Conversion Service is running")
        await asyncio.Future()
    finally:
        await RabbitmqClient.close()


if __name__ == "__main__":
    asyncio.run(main())
