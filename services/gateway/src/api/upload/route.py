from fastapi import APIRouter, Depends
from shared.constants import PRODUCER_CONFIGS, ExchangeNames
from src.dependencies.auth import validate_jwt
from shared.rabbitmq.producer import RabbitmqExchangeProducer

router = APIRouter(prefix="/upload")

@router.post("/", dependencies=[Depends(validate_jwt)])
async def upload_file():
    config = PRODUCER_CONFIGS.get(ExchangeNames.VIDEO_UPLOAD)
    producer = RabbitmqExchangeProducer(
        exchange_config=config
    )
    await producer.init_producer()
    await producer.publish(body="Hello World!", routing_key="upload_file")
    return {"process": "strated"}
