from shared.database.session import create_session_manager
from .url import DATABASE_URL

session_manager = create_session_manager(DATABASE_URL)