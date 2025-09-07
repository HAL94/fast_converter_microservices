from fastapi import APIRouter


router = APIRouter(prefix="/status")

@router.get("/")
def check_status():
    return {"status": "Healthy"}
