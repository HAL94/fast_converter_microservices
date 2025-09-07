from fastapi import APIRouter, Depends
from src.dependencies.auth import validate_jwt
from shared.rabbitmq.producer import RabbitmqBasicProducer
router = APIRouter(prefix="/upload")

@router.post("/", dependencies=[Depends(validate_jwt)])
async def upload_file():
    basic_producer = RabbitmqBasicProducer(queue_name="upload_file")
    await basic_producer.init_producer()
    await basic_producer.publish("Hello World")
    return {"process": "strated"}
