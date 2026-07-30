from fastapi import APIRouter, Request
from pydantic import BaseModel
from app.config.variables import ConfigVariables
from app.ai.prompts.wardrobe_processing import (
    wardrobe_processing_schema,
    wardrobe_processing_system_prompt,
)
from app.ai.openai import llm_call_with_attachments_json
from app.database.queries.wardrobe_items import (
    add_wardrobe_items,
    get_general_wardrobe_items,
    get_model_wardrobe_items,
)
from app.database.queries.models import get_user_model_documents
from app.services.pinecone import upsert_wardrobe_item
from app.services.storage import R2Storage
from typing import Optional
import asyncio

router = APIRouter(prefix="/wardrobe", tags=["Wardrobe"])


# utils function
async def process_single_image(
    img_url: str,
    user_id: str,
    model_id: str | None = None,
):
    metadata = await asyncio.to_thread(
        llm_call_with_attachments_json,
        system_prompt=wardrobe_processing_system_prompt,
        json_schema=wardrobe_processing_schema,
        content=[
            {
                "type": "input_image",
                "image_url": img_url,
            }
        ],
    )

    item_name = metadata.pop("item_name")
    filename = img_url.rsplit("/", 1)[-1]

    wardrobe_item = await add_wardrobe_items(
        user_id=user_id,
        model_id=model_id,
        item_name=item_name,
        metadata=metadata,
        original_image=filename,
    )

    pinecone_wardrobe_item = await upsert_wardrobe_item(
        metadata=metadata,
        item_id=str(wardrobe_item.item_id),
        user_id=user_id,
    )

    if wardrobe_item and pinecone_wardrobe_item:
        return True


class WardrobeUploadRequest(BaseModel):
    img_urls: list[str]
    model_id: Optional[str] = None


class InitUploadRequest(BaseModel):
    file_names: list[str]
    model_id: Optional[str] = None


@router.post("/upload")
async def upload_wardrobe_dress(request: Request, body: WardrobeUploadRequest):
    try:
        user = request.state.user
        user_id = user["id"]

        model_id = body.model_id

        tasks = [
            process_single_image(img_url, user_id, model_id)
            for img_url in body.img_urls
        ]

        metadata_results = await asyncio.gather(*tasks)

        return {
            "success": True,
            "user_id": user_id,
            "results": metadata_results,
        }

    except Exception as e:
        print(f"Unexpected error occurred in upload_wardrobe_dress: {e}")
        return None


@router.post("/init-upload")
async def get_upload_img_auth(request: Request, body: InitUploadRequest):
    try:
        # getting user_id from the request-payload
        user = request.state.user
        user_id = user["id"]

        file_names = body.file_names
        model_id = body.model_id

        upload_creds = []

        if model_id:
            for file_name in file_names:
                r2_creds = R2Storage.get_model_wardrobe_image_url(
                    user_id=user_id, file_name=file_name, model_id=model_id
                )
                upload_creds.append(r2_creds)
        else:
            for file_name in file_names:
                r2_creds = R2Storage.get_general_wardrobe_image_url(
                    user_id=user_id, file_name=file_name
                )
                upload_creds.append(r2_creds)

        return {
            "r2_creds": upload_creds,
        }

    except Exception as e:
        print("Unexpected error occured getting img upload auth as:", e)
        return None


@router.get("/")
async def get_all_user_wardrobe(request: Request):
    try:
        user = request.state.user
        user_id = user["id"]

        wardrobe = []

        # -------------------------
        # General Wardrobe
        # -------------------------
        general_wardrobe_docs = await get_general_wardrobe_items(user_id=user_id)

        general_items = []

        for doc in general_wardrobe_docs:
            general_items.append(
                {
                    "name": doc.item_name,
                    "image_url": R2Storage.get_general_wardrobe_item(
                        user_id=user_id,
                        file_name=doc.images.original_image,
                    ),
                    "item_id": str(doc.item_id),
                }
            )

        wardrobe.append(
            {
                "title": "General",
                "items": general_items,
            }
        )

        # -------------------------
        # Model Wardrobes
        # -------------------------
        all_models = await get_user_model_documents(user_id=user_id)

        for model in all_models:
            model_docs = await get_model_wardrobe_items(
                user_id=user_id,
                model_id=str(model.model_id),
            )

            model_items = []

            for doc in model_docs:
                model_items.append(
                    {
                        "name": doc.item_name,
                        "image_url": R2Storage.get_model_wardrobe_item(
                            user_id=user_id,
                            model_id=str(model.model_id),
                            file_name=doc.images.original_image,
                        ),
                        "item_id": str(doc.item_id),
                    }
                )

            wardrobe.append(
                {
                    "title": model.name,  # replace with model.model_name if that's your field
                    "items": model_items,
                }
            )

        return wardrobe

    except Exception as e:
        print(f"Unexpected error occurred in route function get_all_user_wardrobe: {e}")
        return []
