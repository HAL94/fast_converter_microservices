from fastapi import Response
from shared.schema import UserLogin
from httpx import AsyncClient, Headers
from src.core.config import settings


class AuthServiceClient:
    def __init__(self):
        self.base_url = (
            f"http://{settings.AUTH_SERVICE_HOST}:{settings.AUTH_SERVICE_PORT}"
        )

    async def login(self, data: UserLogin):
        async with AsyncClient(base_url=self.base_url) as client:
            api_response = await client.post("/auth/login", json=data.model_dump())
            return Response(
                content=api_response.content,
                status_code=api_response.status_code,
                headers=api_response.headers,
            )

    async def validate_jwt(self, data: str):
        async with AsyncClient(base_url=self.base_url) as client:
            headers = Headers(headers={"Authorization": f"Bearer {data}"})
            api_response = await client.post("/auth/validate", headers=headers)
            return api_response


__all__ = [AuthServiceClient]
