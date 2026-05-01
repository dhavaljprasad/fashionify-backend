from fastapi import APIRouter
from imagekitio import ImageKit
from app.config.variables import ConfigVariables

router = APIRouter(prefix="/imgkit", tags=["ImgKit"])

imagekit = ImageKit(
    private_key=ConfigVariables.IMGKIT_PRIVATE_KEY,
)


@router.get("/auth")
async def get_upload_token():
    try:
        auth_params = imagekit.helper.get_authentication_parameters()
        return {"auth_params": auth_params}
    except Exception as e:
        print("Unexpected error getting upload token as:", e)
        return
