import enum
from shared.rabbitmq.types import ExchangeConfig, ExchangeReceiverConfig, QueueConfig


class ExchangeNames(enum.StrEnum):
    VIDEO_UPLOAD = "video_upload"


upload_exchange_config = ExchangeConfig(name=ExchangeNames.VIDEO_UPLOAD)


PRODUCER_CONFIGS = {ExchangeNames.VIDEO_UPLOAD: upload_exchange_config}
RECEIVER_CONFIGS = {
    ExchangeNames.VIDEO_UPLOAD: ExchangeReceiverConfig(
        exchange_config=upload_exchange_config,
        binding_keys="upload_file",
        queue_config=QueueConfig(name="", durable=True, exclusive=True),
    )
}
