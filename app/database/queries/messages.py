from app.database.init import Messages
from beanie import PydanticObjectId
from typing import Optional


async def add_image_message(
    conversation_id: str, role: str, text: Optional[str], image_ids: list[str]
):
    try:
        new_image_message_doc = Messages(
            conversation_id=PydanticObjectId(conversation_id),
            role=role,
            text=text if text else None,
            image_ids=image_ids,
        )

        await new_image_message_doc.insert()
        return new_image_message_doc
    except Exception as e:
        print("Unexpected error saving image message as", e)


async def get_all_message(conversation_id: str):
    try:
        conv_id = PydanticObjectId(conversation_id)

        messages = (
            await Messages.find(Messages.conversation_id == conv_id)
            .sort("+timestamp")
            .to_list()
        )

        return messages
    except Exception as e:
        print("Unexpted error occured in mongo function getting all msg as:", e)
        return None
