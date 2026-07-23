from fastapi import APIRouter, Request
from app.database.queries.images import get_latest_user_images
from app.database.queries.models import get_user_model_documents
from app.services.storage import R2Storage

router = APIRouter(prefix="/app", tags=["App"])


@router.get("/models-and-images")
async def get_user_models(request: Request):
    try:
        user = request.state.user
        user_id = user["id"]

        # Pre-uploaded user images (upto 20)
        user_images_docs = await get_latest_user_images(user_id=user_id, limit=20)

        user_images = []
        for img_doc in user_images_docs:
            img_url = R2Storage.get_user_uploaded_images(
                user_id=user_id,
                conversation_id=str(img_doc.conversation_id),
                file_name=img_doc.image_name,
            )
            if img_url:
                user_images.append(img_url)

        # User Models if any
        user_models_docs = await get_user_model_documents(user_id=user_id)

        user_models = []
        for model_doc in user_models_docs:
            img_url = R2Storage.get_user_model_image(
                user_id=user_id, file_name=model_doc.image
            )
            if model_doc.gender == "male":
                model_object = {
                    "name": model_doc.model_name,
                    "image_url": img_url,
                    "gender": "male",
                    "model_id": str(model_doc.model_id),
                }
            elif model_doc.gender == "female":
                model_object = {
                    "name": model_doc.model_name,
                    "image_url": img_url,
                    "gender": "female",
                    "model_id": str(model_doc.model_id),
                }

            user_models.append(model_object)

        return {
            "status": True,
            "data": {"prev_images": user_images, "user_models": user_models},
            "details": "User models fetched successfully",
        }

    except Exception as e:
        print("Unexpected error occured getting user models as:", e)
        return {"status": False, "data": None, "details": "Error getting user models"}
