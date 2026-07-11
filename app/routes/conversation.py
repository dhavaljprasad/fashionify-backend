from fastapi import APIRouter, Request
from pydantic import BaseModel
from typing import Optional, List
from urllib.parse import urlparse
from app.database.queries.conversations import (
    init_new_conversation_document,
    update_conversation_type,
)
from app.database.queries.messages import add_image_message, get_all_message
from app.database.queries.images import save_user_uploaded_images, get_bunch_images_name
from app.database.queries.pooling import init_pooling_doc
from app.database.queries.conversations import get_conversations_by_user_id
from app.utils.imgkit import (
    get_client_upload_auth_params,
    get_user_uploaded_images,
    get_user_generated_images,
)
from app.workers.tasks import prestitched_seeon, link_seeon, dress_up

router = APIRouter(prefix="/conversation", tags=["Conversation"])


class SaveImageRequest(BaseModel):
    conversation_id: str
    file_name: str
    message: Optional[str] = None


class SelectTryOnRequest(BaseModel):
    conversation_id: str
    selected: str


class SeeOnRequest(BaseModel):
    conversation_id: str
    link: str


class DressUpRequest(BaseModel):
    conversation_id: str
    dress: str
    uploaded_images: List[str]
    custom_instruction: str


class SaveSeeOnImageRequest(BaseModel):
    conversation_id: str
    file_name: Optional[str] = None
    text: str


class SaveDressUpImagesRequest(BaseModel):
    conversation_id: str
    text: str
    file_names: List[str] = []


@router.get("/visualization/init")
async def get_visualization_conversation_id(request: Request):
    try:
        # getting user_id from the request-payload
        user = request.state.user
        user_id = user["id"]

        # getting new conversation document
        new_conversation_doc = await init_new_conversation_document(
            user_id=user_id, conversation_type="visualization"
        )

        # getting auth creds for imagekit, client image upload
        imgkit_auth = get_client_upload_auth_params()

        return {
            "conversation_id": str(new_conversation_doc.conversation_id),
            "imgkit_auth": imgkit_auth,
        }

    except Exception as e:
        print("Unexpected error occured generating conversation_id as :", e)
        return None


@router.get("/ai-stylist/init")
async def get_stylist_conversation_id(request: Request):
    try:
        # getting user_id from the request-payload
        user = request.state.user
        user_id = user["id"]

        # getting new conversation document
        new_conversation_doc = await init_new_conversation_document(
            user_id=user_id, conversation_type="stylist"
        )

        return {
            "conversation_id": str(new_conversation_doc.conversation_id),
        }
    except Exception as e:
        print("Unexpected error occured generating conversation_id as: ", e)


@router.get("/init-upload")
async def get_upload_img_auth():
    try:
        # getting auth creds for imagekit, client image upload
        imgkit_auth = get_client_upload_auth_params()

        return {
            "imgkit_auth": imgkit_auth,
        }
    except Exception as e:
        print("Unexpected error occured getting img upload auth as:", e)
        return None


@router.get("/init-multiple-uploads/{number}")
async def get_multiple_img_auth(number: int = 3):
    try:
        imgkit_auths = []
        for _ in range(number):
            imgkit_auth = get_client_upload_auth_params()
            if imgkit_auth:
                imgkit_auths.append(imgkit_auth)

        return {
            "imgkit_auths": imgkit_auths,
        }
    except Exception as e:
        print("Unexpected error occured getting img upload auth as:", e)
        return None


@router.get("/user-conversations")
async def get_all_user_conversations(request: Request):
    try:
        user = request.state.user
        user_id = user["id"]

        user_conversations = await get_conversations_by_user_id(user_id=user_id)
        cleaned_conversations = []
        for conversation in user_conversations:
            cleaned_conversations.append(
                {
                    "conversation_id": str(conversation.conversation_id),
                    "entry_type": conversation.entry_type,
                    "title": conversation.title,
                    "created_at": conversation.created_at,
                    "updated_at": conversation.updated_at,
                    "conversation_type": conversation.conversation_type
                    or "visualization",
                }
            )
        return {"status": "success", "conversations": cleaned_conversations}
    except Exception as e:
        print("Unexpected error occured getting all conversation for user as:", e)
        return None


@router.post("/save-user-image")
async def save_uploaded_image(request: Request, body: SaveImageRequest):
    try:
        # getting user_id from the request-payload
        user = request.state.user
        user_id = user["id"]

        # de-structuring body
        conversation_id = body.conversation_id
        file_name = body.file_name
        message = body.message if body.message is not None else None

        # save user image
        image_doc = await save_user_uploaded_images(
            user_id=user_id, conversation_id=conversation_id, image_name=file_name
        )

        # save image message
        image_message_doc = await add_image_message(
            conversation_id=conversation_id,
            role="user",
            text=message,
            image_ids=[str(image_doc.image_id)],
        )

        # adding the "what do you wanna try-on line"
        ai_message_doc = await add_image_message(
            conversation_id=conversation_id,
            role="ai",
            text="Wonderful, what do you wanna try on?",
            image_ids=[],
        )

        if image_doc and image_message_doc and ai_message_doc:
            return {"status": "success", "saved": True}
        else:
            return {"status": "failure", "saved": False}

    except Exception as e:
        print(
            "Unexpected error occured saving uploaded image and it's message for the conversation as:",
            e,
        )


@router.post("/save-see-on-image")
async def save_see_on_uploaded_image(request: Request, body: SaveSeeOnImageRequest):
    try:
        # getting user_id from the request-payload
        user = request.state.user
        user_id = user["id"]

        # de-structuring body
        conversation_id = body.conversation_id
        file_name = body.file_name
        text = body.text

        image_ids = []
        if file_name:
            # save user image
            image_doc = await save_user_uploaded_images(
                user_id=user_id, conversation_id=conversation_id, image_name=file_name
            )
            if image_doc:
                image_ids = [str(image_doc.image_id)]

        # save image message
        image_message_doc = await add_image_message(
            conversation_id=conversation_id,
            role="user",
            text=text,
            image_ids=image_ids,
        )

        if image_message_doc:
            return {"status": "success", "saved": True}
        else:
            return {"status": "failure", "saved": False}

    except Exception as e:
        print(
            "Unexpected error occured saving uploaded image and it's message for the conversation as:",
            e,
        )


@router.post("/save-dress-up-images")
async def save_dress_up_uploaded_images(
    request: Request, body: SaveDressUpImagesRequest
):
    try:
        # getting user_id from the request-payload
        user = request.state.user
        user_id = user["id"]

        # de-structuring body
        conversation_id = body.conversation_id
        file_names = body.file_names
        text = body.text

        image_ids = []

        for file_doc in file_names:
            if file_doc:
                # save user image
                image_doc = await save_user_uploaded_images(
                    user_id=user_id,
                    conversation_id=conversation_id,
                    image_name=f"{file_doc}.webp",
                )
                if image_doc:
                    image_ids.append(str(image_doc.image_id))

        # save image message
        image_message_doc = await add_image_message(
            conversation_id=conversation_id,
            role="user",
            text=text,
            image_ids=image_ids,
        )

        if image_message_doc:
            return {"status": "success", "saved": True}
        else:
            return {"status": "failure", "saved": False}

    except Exception as e:
        print(
            "Unexpected error occured saving uploaded image and it's message for the conversation as:",
            e,
        )


@router.post("/select-try-on")
async def select_try_on(body: SelectTryOnRequest):
    try:
        new_user_msg_doc = await add_image_message(
            conversation_id=body.conversation_id,
            role="user",
            text=f"I'll go with {body.selected}",
            image_ids=[],
        )

        new_ai_msg_doc = await add_image_message(
            conversation_id=body.conversation_id,
            role="ai",
            text=f"Great, let's try {body.selected}",
            image_ids=[],
        )

        if new_user_msg_doc and new_ai_msg_doc:
            return {"status": "success", "saved": True}
        else:
            return {"status": "failure", "saved": False}

    except Exception as e:
        print("Unexpected error occured setting try-on as:", e)
        return {"status": "failure", "saved": False}


@router.post("/see-on")
async def see_on_generate_image(request: Request, body: SeeOnRequest):
    try:
        # getting user_id from request
        user = request.state.user
        user_id = user["id"]

        # getting params from body
        conversation_id = body.conversation_id
        link = body.link

        # `link` is your input string
        parsed_url = urlparse(link)
        domain = parsed_url.netloc.lower()

        # Check if the link belongs to ImageKit
        if "ik.imagekit.io" in domain:
            updated_conversation_doc = await update_conversation_type(
                conversation_id=conversation_id, conversation_type="prestitched"
            )

            new_pooling_doc = await init_pooling_doc(
                user_id=user_id, pooling_type="see_on"
            )

            prestitched_seeon.delay(
                conversation_id=conversation_id,
                user_id=user_id,
                pooling_id=str(new_pooling_doc.pooling_id),
                link=link,
            )

            if updated_conversation_doc and new_pooling_doc:
                response = {
                    "status": "success",
                    "pooling_id": str(new_pooling_doc.pooling_id),
                }
                return response
            else:
                response = {"status": "faliure", "pooling_id": ""}
                return response

        else:
            print(
                "The provided link does not belong to ImageKit. Proceeding with normal see-on flow."
            )
            print("Provided link:", link)
            updated_conversation_doc = await update_conversation_type(
                conversation_id=conversation_id, conversation_type="link"
            )
            new_pooling_doc = await init_pooling_doc(
                user_id=user_id, pooling_type="see_on"
            )
            link_seeon.delay(
                conversation_id=conversation_id,
                user_id=user_id,
                pooling_id=str(new_pooling_doc.pooling_id),
                link=link,
            )

            if updated_conversation_doc and new_pooling_doc:
                response = {
                    "status": "success",
                    "pooling_id": str(new_pooling_doc.pooling_id),
                }
                return response
            else:
                response = {"status": "faliure", "pooling_id": ""}
                return response

    except Exception as e:
        print("Unexpected error occured generating first see-on image as", e)


@router.post("/dress-up")
async def dress_up_generate_image(request: Request, body: DressUpRequest):
    try:
        # getting user_id from request
        user = request.state.user
        user_id = user["id"]

        # getting params from body
        conversation_id = body.conversation_id
        dress_name = body.dress
        images = body.uploaded_images
        custom_instruction = body.custom_instruction

        updated_conversation_doc = await update_conversation_type(
            conversation_id=conversation_id, conversation_type="clothpiece"
        )

        # init pooling doc
        new_pooling_doc = await init_pooling_doc(
            user_id=user_id, pooling_type="dress_up"
        )

        dress_up.delay(
            conversation_id=conversation_id,
            user_id=user_id,
            pooling_id=str(new_pooling_doc.pooling_id),
            images=images,
            dress_name=dress_name,
            custom_instruction=custom_instruction,
        )

        if updated_conversation_doc and new_pooling_doc:
            response = {
                "status": "success",
                "pooling_id": str(new_pooling_doc.pooling_id),
            }
            return response
        else:
            response = {"status": "faliure", "pooling_id": ""}
            return response

    except Exception as e:
        print("Unexpected error occured generating first see-on image as", e)


@router.get("/{conversation_id}")
async def get_all_conversation_message(request: Request, conversation_id: str):
    try:
        user = request.state.user
        user_id = user["id"]

        all_messages = await get_all_message(conversation_id=conversation_id)

        if not all_messages:
            return {"status": "success", "messages": []}

        cleaned_msgs = []

        for msg in all_messages:
            if msg.image_ids:
                image_names = await get_bunch_images_name(msg.image_ids) or []

                if msg.role == "user":
                    image_urls = [
                        get_user_uploaded_images(
                            user_id=user_id,
                            conversation_id=conversation_id,
                            file_name=name,
                        )
                        for name in image_names
                    ]
                elif msg.role == "ai":
                    image_urls = [
                        get_user_generated_images(
                            user_id=user_id,
                            conversation_id=conversation_id,
                            file_name=name,
                        )
                        for name in image_names
                        if name
                    ]

                new_object = {"role": msg.role, "text": msg.text, "images": image_urls}

            else:
                new_object = {"role": msg.role, "text": msg.text, "images": []}

            cleaned_msgs.append(new_object)

        return {"status": "success", "messages": cleaned_msgs}

    except Exception as e:
        print("Unexpected error occured getting all message conversations as:", e)
        return {"status": "failure", "messages": []}
