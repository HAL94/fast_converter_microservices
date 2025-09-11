from contextlib import asynccontextmanager
from typing import Any, AsyncGenerator, Self
from fastapi import FastAPI
from src.core.minio_client import client
from src.core.config import AppSettings, settings
from src.api import root
from shared.rabbitmq.client import RabbitmqClient
from shared.database import Base
from src.core.files_database import session_manager
from shared.file_database.models import *  # noqa: F403


class FastApp(FastAPI):
    def __init__(self, settings: AppSettings, **kwargs):
        self.settings = settings
        kwargs.setdefault("lifespan", self._lifespan)
        self.title = "Gateway Service"
        self.version = "0.0.1"
        super().__init__(**kwargs)

    async def _connect_rabbitmq(self):
        base_rabbitmq_url = f"amqp://{settings.RABBITMQ_HOST}:{settings.RABBITMQ_PORT}/"
        await RabbitmqClient.connect(
            url=base_rabbitmq_url,
            username=settings.RABBITMQ_USERNAME,
            password=settings.RABBITMQ_PASSWORD,
        )

    def _connect_s3_storage(self):
        if client.ensure_connect():
            print("Minio Client is initialized")

    async def _connect_file_database(self):
        engine = session_manager.engine
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)

    @asynccontextmanager
    async def _lifespan(self, _: Self, /) -> AsyncGenerator[None, Any]:
        await self._connect_rabbitmq()
        await self._connect_file_database()
        self._connect_s3_storage()
        yield
        await RabbitmqClient.close()

    def _setup_middlewares(self) -> None:
        pass

    def _setup_routers(self) -> None:
        self.include_router(root)

    def setup(self) -> None:
        super().setup()

        self._setup_middlewares()
        self._setup_routers()


app = FastApp(settings=settings)
