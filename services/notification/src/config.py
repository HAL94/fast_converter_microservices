from pydantic_settings import BaseSettings


class RabbitMQSettings(BaseSettings):
    RABBITMQ_HOST: str = "localhost"
    RABBITMQ_PORT: int = 5672
    RABBITMQ_USERNAME: str
    RABBITMQ_PASSWORD: str

class MinioSettings(BaseSettings):    
    MINIO_HOST: str
    MINIO_ROOT_USER: str
    MINIO_ROOT_PASSWORD: str

class Settings(RabbitMQSettings, MinioSettings):
    pass

settings = Settings()