from dataclasses import dataclass
import enum

from aio_pika import ExchangeType
from shared.rabbitmq.types import (
    ExchangeConfig,
    ExchangeProducerConfig,
    ExchangeReceiverConfig,
    QueueConfig,
)


class Buckets(enum.StrEnum):
    VIDEO_BUCKET = "videos"


class ExchangeNames(enum.StrEnum):
    VIDEO_UPLOAD = "video_upload"
    CONVERSION = "conversion"


class BindingKeys(enum.StrEnum):
    UPLOAD_FILE = "upload_file"


upload_exchange_config = ExchangeConfig(name=ExchangeNames.VIDEO_UPLOAD)
convert_completed_exchange_config = ExchangeConfig(
    name=ExchangeNames.CONVERSION, exchange_type=ExchangeType.FANOUT
)


@dataclass
class ProducerConfigs:
    VideoUpload = ExchangeProducerConfig(exchange_config=upload_exchange_config)
    ConvertCompleted = ExchangeReceiverConfig(
        exchange_config=convert_completed_exchange_config
    )


@dataclass
class ReceiverConfigs:
    VideoUpload = ExchangeReceiverConfig(
        exchange_config=upload_exchange_config,
        binding_keys=BindingKeys.UPLOAD_FILE,
        queue_config=QueueConfig(name="", durable=True, exclusive=True),
    )
    ConvertCompleted = ExchangeReceiverConfig(
        exchange_config=convert_completed_exchange_config,
        binding_keys="",
        queue_config=QueueConfig(exclusive=True),
    )
