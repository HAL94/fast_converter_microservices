from fastapi import APIRouter

router = APIRouter(prefix="/upload")

@router.post("/")
async def upload_file():
    return {"process": "strated"}
