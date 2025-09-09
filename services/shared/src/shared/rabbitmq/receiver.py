import asyncio
from typing import Optional


from shared.rabbitmq.types import ExchangeReceiverConfig, QueueConfig
from .base import OnMessageCallback, RabbitmqReceiverBase


class RabbitmqBasicReceiver(RabbitmqReceiverBase):
    def __init__(self, queue_config: QueueConfig):
        super().__init__()
        self.queue_config = queue_config

    async def init_receiver(self):
        try:
            return await self.declare_queue()
        except Exception as e:
            print(f"Failed to init receiver: {e}")
            raise e

    async def declare_queue(self, durable: Optional[bool] = None):
        self.queue = await self.channel.declare_queue(
            name=self.queue_config.name,
            durable=durable if durable is not None else self.queue_config.durable,
        )
        return self.queue

    async def set_qos(self, prefetch_count: int):
        return await self.channel.set_qos(prefetch_count=prefetch_count)

    async def consume(self, callback: OnMessageCallback, no_ack: bool = False) -> None:
        if not self.queue:
            raise ValueError("[RabbitmqBasicReceiver]: Queue was not declared")
        await self.queue.consume(callback=callback, no_ack=no_ack)


class RabbitmqExchangeReceiver(RabbitmqReceiverBase):
    def __init__(self, config: ExchangeReceiverConfig):
        super().__init__()
        self.exchange_config = config.exchange_config
        self.exchange = None
        self.queue_config = config.queue_config
        self.binding_keys = config.binding_keys

    async def init_receiver(self):
        self.exchange = await self.channel.declare_exchange(
            name=self.exchange_config.name,
            type=self.exchange_config.exchange_type,
            durable=self.exchange_config.durable,
        )

        if not self.exchange:
            raise ValueError("[RabbitmqExchangeReceiver]: Failed to declare exchange")

        self.queue = await self.channel.declare_queue(
            name=self.queue_config.name,
            exclusive=self.queue_config.exclusive,
        )

        if not self.queue:
            raise ValueError("[RabbitmqExchangeReceiver]: Failed to declare queue")

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
        return await asyncio.gather(binding_tasks)

    async def set_qos(self, prefetch_count: int):
        return await self.channel.set_qos(prefetch_count=prefetch_count)

    async def consume(self, callback, no_ack=False) -> str:
        if not self.queue:
            raise ValueError(
                "[RabbitmqExchangeReceiver]: Queue was not declared. Make sure to call init_receiver"
            )
        return await self.queue.consume(callback=callback, no_ack=no_ack)
