from src.core.config import settings
from sqlalchemy import URL

DATABASE_URL = URL.create(
    drivername="postgresql+asyncpg",
    username=settings.FILE_PG_USER,
    password=settings.FILE_PG_PW,
    host=settings.FILE_PG_HOST,
    port=settings.FILE_PG_PORT,
    database=settings.FILE_PG_DB,
)
