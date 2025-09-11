from src.core.files_database import session_manager as file_session_manager


async def get_filedb_async_session():
    async with file_session_manager.session() as session:
        yield session
