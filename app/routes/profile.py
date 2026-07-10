from fastapi import APIRouter, Request
from pydantic import BaseModel
from typing import Optional
from app.database.queries.users import update_user_profile
from app.utils.auth import create_access_token
from fastapi.responses import JSONResponse

router = APIRouter(prefix="/profile", tags=["Auth"])


class UpdateRequestType(BaseModel):
    name: str
    type_of_user: str
    bussiness_name: Optional[str] = None
    bussiness_address: Optional[str] = None


@router.post("/update")
async def update_user_details_function(request: Request, body: UpdateRequestType):
    try:
        # getting user_id from the request-payload
        user = request.state.user
        user_id = user["id"]

        name = body.name
        type_of_user = body.type_of_user
        bussiness_name = body.bussiness_name
        bussiness_address = body.bussiness_address

        updated_user_doc = await update_user_profile(
            user_id=user_id,
            name=name,
            type_of_user=type_of_user,
            bussiness_name=bussiness_name,
            bussiness_address=bussiness_address,
        )

        if updated_user_doc:
            token_data = {
                "id": str(updated_user_doc.user_id),
                "name": updated_user_doc.name,
                "email": updated_user_doc.email,
                "image_url": updated_user_doc.image_url,
                "type_of_user": updated_user_doc.type_of_user,
                "bussiness_name": updated_user_doc.bussiness_name,
                "bussiness_address": updated_user_doc.bussiness_address,
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
                secure=False,  # True in prod
                samesite="lax",
                max_age=60 * 60 * 24 * 30,
                path="/",
            )

            return response

    except Exception as e:
        print("Unexpected error occured updating the user details as :", e)
        return None
