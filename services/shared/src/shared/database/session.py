from typing import Any, AsyncIterator
from sqlalchemy.ext.asyncio import (
    create_async_engine,
    async_sessionmaker,
    AsyncEngine,
    AsyncSession,
)
from contextlib import asynccontextmanager
from sqlalchemy import URL


class SessionManager:
    def __init__(self, host: URL, /, *, kwargs: dict[str, Any] | None = None) -> None:
        if kwargs is None:
            kwargs = {}

        self.engine: AsyncEngine | None = create_async_engine(host, **kwargs)
        self._session_maker: async_sessionmaker[AsyncSession] | None = (
            async_sessionmaker(
                autocommit=False,
                bind=self.engine,
                expire_on_commit=False,
            )
        )

    async def close(self) -> None:
        if self.engine is None:
            raise Exception("DatabaseSessionManager is not initialized")

        await self.engine.dispose()

        self.engine = None
        self._session_maker = None

    @asynccontextmanager
    async def session(self) -> AsyncIterator[AsyncSession]:
        if self._session_maker is None:
            raise Exception("DatabaseSessionManager is not initialized")

        session = self._session_maker()
        try:
            yield session
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


# file_session_manager = FileDbSessionManager(
#     DATABASE_URL,
#     kwargs={
#         "echo": False,
#     },
# )

# async def get_filedb_async_session():
#     async with file_session_manager.session() as session:
#         yield session
