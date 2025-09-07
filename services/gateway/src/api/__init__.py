from fastapi import APIRouter

from src.api.status.route import router as status_route
from src.api.auth.route import router as auth_route
from src.api.upload.route import router as upload_route

root = APIRouter(prefix="/api/v1")

root.include_router(status_route)
root.include_router(auth_route)
root.include_router(upload_route)

__all__ = [root]