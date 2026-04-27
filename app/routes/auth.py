from fastapi import APIRouter
from pydantic import BaseModel
import traceback

router = APIRouter(prefix="/auth", tags=["Auth"])


class AuthSigninRequest(BaseModel):
    credential: str


@router.post("/")
async def auth_signin(data: AuthSigninRequest):
    try:
        print(data)
    except Exception as e:
        traceback.format_exc()
        print(f"Unexpected error occured: {e}")
        return {"status": False, "data": None, "details": "Unexpected error occured"}
