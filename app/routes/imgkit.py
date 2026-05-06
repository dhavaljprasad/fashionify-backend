from fastapi import APIRouter
from app.utils.imgkit import get_client_upload_auth_params

router = APIRouter(prefix="/imgkit", tags=["ImgKit"])


@router.get("/auth")
async def get_upload_token():
    try:
        auth_params = get_client_upload_auth_params
        if auth_params:
            return {"auth_params": auth_params}
    except Exception as e:
        print("Unexpected error getting upload token as:", e)
        return
