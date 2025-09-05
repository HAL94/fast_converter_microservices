from pydantic_settings import BaseSettings, SettingsConfigDict

class AppConfigSettings(BaseSettings):
    ENV: str = "prod"
    APP_PORT: int = 8000
    HOST: str = "localhost"

class PostgresSettings(BaseSettings):
    PG_USER: str
    PG_PW: str
    PG_SERVER: str
    PG_PORT: str
    PG_DB: str

class AuthSettings(BaseSettings):
    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int

class Settings(PostgresSettings, AuthSettings, AppConfigSettings):
    model_config = SettingsConfigDict(
        env_file='.env', env_file_encoding='utf-8')
    
settings = Settings()