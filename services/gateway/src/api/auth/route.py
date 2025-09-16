from fastapi import APIRouter, Depends
from src.dependencies.auth import ValidateJwt, get_auth_client
from shared.schema import UserLogin
from src.services.auth import AuthServiceClient

router = APIRouter(prefix="/auth")


@router.post("/login")
async def login(
    data: UserLogin, auth_client: AuthServiceClient = Depends(get_auth_client)
):
    return await auth_client.login(data)


@router.get("/protected", dependencies=[Depends(ValidateJwt())])
async def access_protocted():
    return {"success": "From gateway"}
