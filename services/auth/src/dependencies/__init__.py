from src.models import SessionLocal
# Database dependency
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()