from fastapi import APIRouter, Request
from app.database.queries.conversations import init_new_conversation_document
from app.database.queries.messages import add_image_message, get_all_message
from app.database.queries.images import save_user_uploaded_images, get_bunch_images_name
from app.utils.imgkit import get_client_upload_auth_params, get_user_uploaded_images
from pydantic import BaseModel

router = APIRouter(prefix="/conversation", tags=["Conversation"])


class SaveImageRequest(BaseModel):
    conversation_id: str
    file_name: str


class SelectTryOnRequest(BaseModel):
    conversation_id: str
    selected: str


@router.get("/init")
async def get_conversation_id(request: Request):
    try:
        # getting user_id from the request-payload
        user = request.state.user
        user_id = user["id"]

        # getting new conversation document
        new_conversation_doc = await init_new_conversation_document(user_id=user_id)

        # getting auth creds for imagekit, client image upload
        imgkit_auth = get_client_upload_auth_params()

        return {
            "conversation_id": str(new_conversation_doc.conversation_id),
            "imgkit_auth": imgkit_auth,
        }

    except Exception as e:
        print("Unexpected error occured generating conversation_id as :", e)
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

        # save user image
        image_doc = await save_user_uploaded_images(
            user_id=user_id, conversation_id=conversation_id, image_name=file_name
        )

        # save image message
        image_message_doc = await add_image_message(
            conversation_id=conversation_id,
            role="user",
            text=None,
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

                image_urls = [
                    get_user_uploaded_images(
                        user_id=user_id, conversation_id=conversation_id, file_name=name
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
