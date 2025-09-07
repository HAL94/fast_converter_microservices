from pydantic_settings import BaseSettings, SettingsConfigDict

class RabbitMQSettings(BaseSettings):
    RABBITMQ_HOST: str = "localhost"
    RABBITMQ_PORT: int = 5672
    RABBITMQ_USERNAME: str
    RABBITMQ_PASSWORD: str

class AuthServiceSettings(BaseSettings):
    AUTH_SERVICE_HOST: str
    AUTH_SERVICE_PORT: int


class BaseAppSettings(BaseSettings):
    ALLOWED_ORIGIN: str = "*"
    APP_PORT: int
    ENV: str = "PROD"


class AppSettings(BaseAppSettings, RabbitMQSettings, AuthServiceSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")


settings = AppSettings()
