import aio_pika
from aio_pika.abc import AbstractRobustQueue
from aiormq.abc import ConfirmationFrameType

from .base import RabbitmqProducerBase
from .types import ExchangeConfig, QueueConfig

class RabbitmqBasicProducer(RabbitmqProducerBase):
    def __init__(self, queue_config: QueueConfig):
        super().__init__()
        self.queue_config = queue_config

    async def init_producer(self):
        try:
            await self.declare_queue()
        except Exception as e:
            print(f"Failed to init producer: {e}")
            raise e

    async def declare_queue(self) -> AbstractRobustQueue:
        self.queue = await self.channel.declare_queue(
            name=self.queue_config.name, durable=self.queue_config.durable
        )
        return self.queue

    async def publish(self, body: str) -> ConfirmationFrameType | None:
        message = aio_pika.Message(body=body.encode("utf-8"))
        return await self.channel.default_exchange.publish(
            message=message, routing_key=self.queue_config.name
        )

class RabbitmqExchangeProducer(RabbitmqProducerBase):
    def __init__(self, exchange_config: ExchangeConfig):
        super().__init__()
        self.exchange_config = exchange_config
        self.exchange = None

    async def init_producer(self):
        self.exchange = await self.channel.declare_exchange(
            name=self.exchange_config.name,
            type=self.exchange_config.exchange_type,
            durable=self.exchange_config.durable,
        )

    async def publish(self, body: str, routing_key: str = "", **kwargs):
        if not self.exchange:
            raise ValueError("[RabbitmqExchangeProducer]: Exchange was not declared")
        message = aio_pika.Message(body=body.encode("utf-8")) 
        # routing_key should be ignored in the case of 'fanout'
        return await self.exchange.publish(message=message, routing_key=routing_key)
