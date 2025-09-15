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

class FileDbSettings(BaseSettings):
    FILE_PG_DB: str
    FILE_PG_USER: str
    FILE_PG_PW: str
    FILE_PG_PORT: int
    FILE_PG_HOST: str

class ResendSettings(BaseSettings):
    EMAIL_SERVICE: str
    DEV_EMAIL: str

class GatewaySettings(BaseSettings):
    GATEWAY_API_DOWNLOAD: str

class Settings(RabbitMQSettings, MinioSettings, FileDbSettings, ResendSettings, GatewaySettings):
    pass

settings = Settings()