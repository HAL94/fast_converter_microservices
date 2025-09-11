from fastapi import HTTPException, Request
from src.services.auth import AuthServiceClient


def get_auth_client():
    return AuthServiceClient()


async def validate_jwt(request: Request, get_payload: bool = True):
    client_auth = AuthServiceClient()
    UNAUTH_EXCPETION = HTTPException(status_code=401, detail="Unauthorized")

    auth_header = request.headers.get("Authorization")

    if not auth_header:
        raise UNAUTH_EXCPETION

    token: str = auth_header.split(" ")[1]

    if not token:
        raise UNAUTH_EXCPETION

    api_response = await client_auth.validate_jwt(token)

    if api_response.status_code == 401:
        raise UNAUTH_EXCPETION
    
    if get_payload:
        return api_response.json()
    
