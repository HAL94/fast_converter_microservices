from pydantic_settings import BaseSettings, SettingsConfigDict


class RabbitMQSettings(BaseSettings):
    RABBITMQ_HOST: str = "localhost"
    RABBITMQ_PORT: int = 5672
    RABBITMQ_USERNAME: str
    RABBITMQ_PASSWORD: str


class AuthServiceSettings(BaseSettings):
    AUTH_SERVICE_HOST: str
    AUTH_SERVICE_PORT: int


class MinioSettings(BaseSettings):
    MINIO_HOST: str
    MINIO_ROOT_USER: str
    MINIO_ROOT_PASSWORD: str


class BaseAppSettings(BaseSettings):
    ALLOWED_ORIGIN: str = "*"
    APP_PORT: int
    ENV: str = "PROD"


class FileDbPostgres(BaseSettings):
    FILE_PG_DB: str
    FILE_PG_USER: str
    FILE_PG_PW: str
    FILE_PG_PORT: int
    FILE_PG_HOST: str


class AppSettings(
    BaseAppSettings,
    MinioSettings,
    RabbitMQSettings,
    FileDbPostgres,
    AuthServiceSettings,
):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")


settings = AppSettings()
