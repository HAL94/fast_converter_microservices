import aio_pika
from abc import ABC, abstractmethod
import asyncio
from typing import Any, Awaitable, Callable, Coroutine, TypeAlias, Union
from aiormq import spec

from .base import RabbitmqBase

OnMessageCallback: TypeAlias = Callable[[aio_pika.IncomingMessage], Awaitable[Any]]


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
    
class RabbitmqBasicReceiver(RabbitmqReceiverBase):
    def __init__(self, queue_name: str):
        super().__init__()
        self.queue_name = queue_name

    async def init_receiver(self):
        try:
            return await self.declare_queue()
        except Exception as e:
            print(f"Failed to init receiver: {e}")
            raise e

    async def declare_queue(self, durable: bool = True):
        self.queue = await self.channel.declare_queue(
            name=self.queue_name, durable=durable
        )
        return self.queue

    async def set_qos(self, prefetch_count: int):
        return await self.channel.set_qos(prefetch_count=prefetch_count)

    async def consume(self, callback: OnMessageCallback, no_ack: bool = False) -> None:
        if not self.queue:
            raise ValueError("Queue was not declared")
        await self.queue.consume(callback=callback, no_ack=no_ack)


class RabbitmqDirectReceiver(RabbitmqReceiverBase):
    def __init__(self, exchange_name: str, binding_keys: Union[str | list[str]]):
        super().__init__()
        self.exchange_name = exchange_name
        self.binding_keys = binding_keys

    async def init_receiver(self):
        try:
            await self.declare_exchange()
            await self.declare_queue()
            await self.bind_queue()
        except Exception as e:
            raise e
            

    async def declare_queue(self, exclusive: bool = True):
        self.queue = await self.channel.declare_queue(name="", exclusive=exclusive)        
        return self.queue
        

    async def declare_exchange(self, durable: bool = True):
        self.exchange = await self.channel.declare_exchange(
            name=self.exchange_name, type=aio_pika.ExchangeType.DIRECT, durable=durable
        )
        return self.exchange

    async def bind_queue(
        self
    ) -> spec.Queue.BindOk | list[spec.Queue.BindOk]:
        if not self.queue:
            raise ValueError("Queue was not declared")

        if isinstance(self.binding_keys, str):
            return await self.queue.bind(
                exchange=self.exchange, routing_key=self.binding_keys
            )

        binding_tasks = []
        for key in self.binding_keys:
            binding_tasks.append(
                self.queue.bind(
                    exchange=self.exchange,
                    routing_key=key,
                )
            )

        return await asyncio.gather(*binding_tasks)

    async def consume(self, callback: OnMessageCallback, no_ack: bool = False) -> str:
        if not self.queue:
            raise ValueError("Queue was not declared")

        return await self.queue.consume(callback=callback, no_ack=no_ack)        
