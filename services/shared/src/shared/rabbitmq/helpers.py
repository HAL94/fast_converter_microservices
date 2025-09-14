

from shared.rabbitmq.producer import RabbitmqExchangeProducer
from shared.rabbitmq.receiver import RabbitmqExchangeReceiver
from shared.rabbitmq.types import ExchangeReceiverConfig, ExchangeProducerConfig


async def create_exchange_producer(config: ExchangeProducerConfig):
    producer = RabbitmqExchangeProducer(config=config)
    await producer.init_producer()

    return producer

async def create_exchange_receiver(config: ExchangeReceiverConfig):
    receiver = RabbitmqExchangeReceiver(config=config)
    await receiver.init_receiver()

    return receiver