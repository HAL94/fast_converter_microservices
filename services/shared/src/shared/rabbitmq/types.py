from typing import Optional, Union

import aio_pika
from pydantic import BaseModel, Field


class ExchangeConfig(BaseModel):
    name: str
    exchange_type: aio_pika.ExchangeType = Field(default=aio_pika.ExchangeType.DIRECT)
    durable: bool = Field(default=True)
    


class QueueConfig(BaseModel):
    name: str = Field(default="")
    durable: bool = Field(default=True)
    exclusive: bool = Field(default=False)
    


class ExchangeReceiverConfig(BaseModel):
    exchange_config: ExchangeConfig
    binding_keys: Union[str | list[str]]
    queue_config: Optional[QueueConfig] = Field(default=QueueConfig(exclusive=True))

