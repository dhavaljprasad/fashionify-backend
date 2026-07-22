from fastapi import APIRouter, Request
from pydantic import BaseModel
from app.database.models.models import MaleMeasurements, FemaleMeasurements
from app.database.queries.models import (
    init_new_model_document,
    get_user_model_documents,
    delete_model_document_by_id,
    update_model_measurements,
)
from app.utils.imgkit import get_user_model_image, get_client_upload_auth_params
from app.services.storage import R2Storage
from app.services.storage import R2Storage

router = APIRouter(prefix="/model", tags=["User Models"])


class InitModelRequest(BaseModel):
    gender: str
    image: str
    model_name: str
    measurements: MaleMeasurements | FemaleMeasurements


class UpdateModelRequest(BaseModel):
    model_id: str
    gender: str
    measurements: dict


class ImageUploadRequest(BaseModel):
    file_name: str


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
        model_list = []
        if model_docs and len(model_docs) > 0:
            for model in model_docs:
                image_url = R2Storage.get_user_model_image(
                    user_id=user_id, file_name=model.image
                )

                if model.gender == "male":
                    model_object = {
                        "name": model.model_name,
                        "gender": model.gender,
                        "image_url": image_url,
                        "model_id": str(model.model_id),
                        "measurements": model.male_measurements,
                    }
                elif model.gender == "female":
                    model_object = {
                        "name": model.model_name,
                        "gender": model.gender,
                        "image_url": image_url,
                        "model_id": str(model.model_id),
                        "measurements": model.female_measurements,
                    }
                model_list.append(model_object)

        return {"status": "success", "models": model_list}
    except Exception as e:
        print("Unexpected error occured getting user models as:", e)
        return {"status": "failure", "models": []}


@router.post("/img-upload")
async def get_image_creds_function(request: Request, body: ImageUploadRequest):
    try:
        user = request.state.user
        user_id = user["id"]

        file_name = body.file_name

        if user_id:
            r2_creds = R2Storage.get_model_image_presigned_url(
                user_id=user_id, file_name=file_name
            )

            return {
                "r2_creds": r2_creds,
            }
    except Exception as e:
        print("Unexpected error occured getting upload image auth as: ", e)


@router.put("/update")
async def update_user_model_measurements(request: Request, body: UpdateModelRequest):
    try:
        user = request.state.user
        user_id = user["id"]

        if not body.model_id or not body.gender:
            return {
                "status": "failure",
                "updated": False,
                "details": "model_id and gender are required",
            }

        updated_model = await update_model_measurements(
            model_id=body.model_id,
            gender=body.gender,
            measurements=body.measurements,
        )

        if updated_model:
            return {
                "status": "success",
                "updated": True,
                "details": "Model measurements updated successfully",
            }

        return {
            "status": "failure",
            "updated": False,
            "details": "Failed to update model measurements",
        }
    except Exception as e:
        print("Unexpected error occured updating user model as:", e)
        return {
            "status": "failure",
            "updated": False,
            "details": "Error updating model measurements",
        }


@router.delete("/{model_id}")
async def delete_user_model_function(request: Request, model_id: str):
    try:

        # getting user_id from the request-payload
        user = request.state.user
        user_id = user["id"]

        if not model_id:
            return {
                "status": "failure",
                "deleted": False,
                "details": "model_id is required",
            }

        deleted = await delete_model_document_by_id(model_id=model_id, user_id=user_id)
        if deleted:
            return {
                "status": "success",
                "deleted": True,
                "details": "Model deleted successfully",
            }

        return {
            "status": "failure",
            "deleted": False,
            "details": "Failed to delete model",
        }
    except Exception as e:
        print("Unexpected error occured deleting user model as:", e)
        return {
            "status": "failure",
            "deleted": False,
            "details": "Error deleting model",
        }
