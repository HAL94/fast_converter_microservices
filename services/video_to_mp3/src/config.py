

from pydantic_settings import BaseSettings

class FileDbSettings(BaseSettings):        
    FILE_PG_USER: str
    FILE_PG_PW: str
    FILE_PG_HOST: str
    FILE_PG_PORT: str
    FILE_PG_DB: str

class MinioSettings(BaseSettings):
    MINIO_HOST: str
    MINIO_ROOT_USER: str
    MINIO_ROOT_PASSWORD: str

class RabbitMQSettings(BaseSettings):
    RABBITMQ_HOST: str = "localhost"
    RABBITMQ_PORT: int = 5672
    RABBITMQ_USERNAME: str
    RABBITMQ_PASSWORD: str

class Settings(FileDbSettings, MinioSettings, RabbitMQSettings):
    pass

settings = Settings()