from aio_pika.abc import AbstractConnection, AbstractChannel
from .client import RabbitmqClient


class RabbitmqBase:
    def __init__(self):
        self.connection: AbstractConnection = RabbitmqClient.connection
        self.channel: AbstractChannel = RabbitmqClient.channel
        if not self.connection or not self.channel:
            raise ConnectionError(
                "RabbitmqClient is not connected. Call RabbitmqClient.connect() first."
            )
