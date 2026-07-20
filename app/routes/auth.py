from fastapi import APIRouter, Request, HTTPException, status
from fastapi.responses import JSONResponse
from pydantic import BaseModel
import traceback

from app.utils.auth import verify_google_creds, create_access_token
from app.database.queries.users import save_or_update_user

router = APIRouter(prefix="/auth", tags=["Auth"])


class AuthSigninRequest(BaseModel):
    credential: str


@router.post("/sign-in")
async def auth_signin(data: AuthSigninRequest):
    try:

        # getting user details using creds
        id_info = await verify_google_creds(data.credential)

        # structuring user details based on our user schema
        user = {
            "name": id_info["name"],
            "email": id_info["email"],
            "image_url": id_info["picture"] or "",
            "provider_user_id": id_info["sub"],
            "provider": "google",
        }

        # saving or updating user in the db
        saved_user = await save_or_update_user(user_dict=user)

        token_data = {
            "id": str(saved_user.user_id),
            "name": saved_user.name,
            "email": saved_user.email,
            "image_url": saved_user.image_url,
            "type_of_user": saved_user.type_of_user,
            "bussiness_name": saved_user.bussiness_name,
            "bussiness_address": saved_user.bussiness_address,
        }

        access_token = create_access_token(token_data)

        response = JSONResponse(
            content={
                "status": True,
                "data": {"access_token": access_token},
                "details": "User signed-in successfully",
            }
        )

        response.set_cookie(
            key="access_token",
            value=access_token,
            httponly=True,
            secure=True,  # True in prod
            samesite="lax",
            domain=".fashionifyai.app",
            max_age=60 * 60 * 24 * 30,
            path="/",
        )

        return response

    except Exception as e:
        traceback.format_exc()
        print(f"Unexpected error occured: {e}")
        return {"status": False, "data": None, "details": "Unexpected error occured"}


@router.get("/me")
async def get_me(request: Request):
    user = request.state

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
        )

    return {
        "status": True,
        "data": user.user,  # _state.user
        "details": "User fetched successfully",
    }


@router.post("/logout")
async def logout():
    response = JSONResponse(
        content={
            "status": True,
            "details": "Logged out successfully",
        }
    )

    response.delete_cookie(
        key="access_token",
        path="/",
        # include these for consistency with how you set it
        samesite="lax",
        secure=False,  # True in production (HTTPS)
    )

    return response
