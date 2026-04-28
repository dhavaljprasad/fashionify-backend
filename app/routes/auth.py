from fastapi import APIRouter
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

        print(id_info, "working till hereeeeeee")

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

        print(saved_user, "working till here")

        token_data = {
            "id": str(saved_user.user_id),
            "name": saved_user.name,
            "email": saved_user.email,
            "image_url": saved_user.image_url,
            "type_of_user": saved_user.type_of_user,
        }

        access_token = create_access_token(token_data)
        return {
            "status": True,
            "data": {"access_token": access_token},
            "details": "User signed-in successfully",
        }

    except Exception as e:
        traceback.format_exc()
        print(f"Unexpected error occured: {e}")
        return {"status": False, "data": None, "details": "Unexpected error occured"}
