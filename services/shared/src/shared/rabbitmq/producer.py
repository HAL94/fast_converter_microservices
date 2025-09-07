from abc import ABC, abstractmethod
from typing import Any, Coroutine
import aio_pika
from aio_pika.abc import AbstractRobustQueue, AbstractRobustExchange
from aiormq.abc import ConfirmationFrameType

from .base import RabbitmqBase


class RabbitmqProducerBase(ABC, RabbitmqBase):
    @abstractmethod
    def publish(self, exchange: str, routing_key: str, body: str | bytes) -> None:
        raise NotImplementedError()

    @abstractmethod
    async def init_producer(self) -> Coroutine[Any, Any, Any]:
        raise NotImplementedError()


class RabbitmqDirectProducer(RabbitmqProducerBase):
    def __init__(self, exchange_name: str):
        super().__init__()
        self.exchange_name = exchange_name
    
    async def init_producer(self):
        try:
            await self.declare_exchange()
        except Exception as e:
            raise e

    async def declare_exchange(self, durable=True) -> AbstractRobustExchange:
        self.exchange = await self.channel.declare_exchange(
            name=self.exchange_name, type=aio_pika.ExchangeType.DIRECT, durable=durable
        )
        return self.exchange

    async def publish(
        self, routing_key: str, body: str
    ) -> ConfirmationFrameType | None:
        if not self.exchange:
            raise ValueError("Exchange was not declared")
        message = aio_pika.Message(body=body.encode("utf-8"))
        return await self.exchange.publish(message=message, routing_key=routing_key)


class RabbitmqBasicProducer(RabbitmqProducerBase):
    def __init__(self, queue_name: str):
        super().__init__()
        self.queue_name = queue_name

    async def init_producer(self):
        try:
            await self.declare_queue()
        except Exception as e:
            print(f"Failed to init producer: {e}")
            raise e

    async def declare_queue(self, durable: bool = True) -> AbstractRobustQueue:
        self.queue = await self.channel.declare_queue(name=self.queue_name, durable=durable)
        return self.queue

    async def publish(self, body: str) -> ConfirmationFrameType | None:
        message = aio_pika.Message(body=body.encode("utf-8"))
        return await self.channel.default_exchange.publish(
            message=message, routing_key=self.queue.name
        )
