from abc import ABC, abstractmethod
from typing import Any, Awaitable, Callable, Coroutine, TypeAlias
import aio_pika
from aio_pika.abc import AbstractConnection, AbstractChannel
from .client import RabbitmqClient

OnMessageCallback: TypeAlias = Callable[[aio_pika.IncomingMessage], Awaitable[Any]]

class RabbitmqBase:
    def __init__(self):
        self.connection: AbstractConnection = RabbitmqClient.connection
        self.channel: AbstractChannel = RabbitmqClient.channel
        if not self.connection or not self.channel:
            raise ConnectionError(
                "RabbitmqClient is not connected. Call RabbitmqClient.connect() first."
            )

class RabbitmqReceiverBase(ABC, RabbitmqBase):
    @abstractmethod
    def consume(
        self,
        no_ack: bool,
        callback: OnMessageCallback,
    ) -> None:
        raise NotImplementedError()

    @abstractmethod
    async def init_receiver(self) -> Coroutine[Any, Any, Any]:
        raise NotImplementedError()
    
class RabbitmqProducerBase(ABC, RabbitmqBase):
    @abstractmethod
    def publish(self, exchange: str, routing_key: str, body: str | bytes) -> None:
        raise NotImplementedError()

    @abstractmethod
    async def init_producer(self) -> Coroutine[Any, Any, Any]:
        raise NotImplementedError()