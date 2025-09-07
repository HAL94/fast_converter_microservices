from contextlib import asynccontextmanager
from typing import Any, AsyncGenerator, Self
from fastapi import FastAPI
from src.core.config import AppSettings, settings
from src.api import root


class FastApp(FastAPI):
    def __init__(self, settings: AppSettings, **kwargs):
        self.settings = settings
        kwargs.setdefault("lifespan", self._lifespan)
        self.title = "Gateway Service"
        self.version = "0.0.1"
        super().__init__(**kwargs)

    @asynccontextmanager
    async def _lifespan(self, _: Self, /) -> AsyncGenerator[None, Any]:
        yield

    def _setup_middlewares(self) -> None:
        pass

    def _setup_routers(self) -> None:
        self.include_router(root)

    def setup(self) -> None:
        super().setup()

        self._setup_middlewares()
        self._setup_routers()


app = FastApp(settings=settings)
