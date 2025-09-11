from shared.database import SessionManager
from .url import DATABASE_URL

session_manager = SessionManager(DATABASE_URL)