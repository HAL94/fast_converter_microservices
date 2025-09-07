from fastapi import APIRouter, Depends
from src.dependencies import get_auth_client, validate_jwt
from shared.schema import UserLogin
from src.services.auth import AuthServiceClient

router = APIRouter(prefix="/auth")


@router.post("/login")
async def login(
    data: UserLogin, auth_client: AuthServiceClient = Depends(get_auth_client)
):
    return await auth_client.login(data)


@router.get("/protected", dependencies=[Depends(validate_jwt)])
async def access_protocted():
    return {"success": "From gateway"}
