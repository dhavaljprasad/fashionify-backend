from fastapi import APIRouter, Request
from pydantic import BaseModel
from app.database.models.models import MaleMeasurements, FemaleMeasurements
from app.database.queries.models import (
    init_new_model_document,
    get_user_model_documents,
)

router = APIRouter(prefix="/model", tags=["User Models"])


class InitModelRequest(BaseModel):
    gender: str
    image: str
    model_name: str
    measurements: MaleMeasurements | FemaleMeasurements


@router.post("/init")
async def init_user_model(request: Request, body: InitModelRequest):
    try:
        # getting user_id from the request-payload
        user = request.state.user
        user_id = user["id"]

        new_model = await init_new_model_document(
            user_id=user_id,
            gender=body.gender,
            image=body.image,
            model_name=body.model_name,
            measurements=body.measurements,
        )
        if new_model:
            return {"status": "success", "saved": True}
        else:
            return {"status": "failure", "saved": False}
    except Exception as e:
        print("Unexpected error occured init the new user-model as:", e)
        return None


@router.get("/")
async def get_user_models_function(request: Request):
    try:
        user = request.state.user
        user_id = user["id"]

        model_docs = await get_user_model_documents(user_id=user_id)
        return {"status": "success", "models": model_docs}
    except Exception as e:
        print("Unexpected error occured getting user models as:", e)
        return {"status": "failure", "models": []}
