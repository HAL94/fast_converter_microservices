from .settings import settings
from sqlalchemy import URL

DATABASE_URL = URL.create(drivername="postgresql",
                          username=settings.PG_USER,
                          password=settings.PG_PW,
                          host=settings.PG_SERVER,
                          port=settings.PG_PORT,
                          database=settings.PG_DB)