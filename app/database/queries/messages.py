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


async def get_first_message(conversation_id: str):
    try:
        conv_id = PydanticObjectId(conversation_id)

        message = (
            await Messages.find(Messages.conversation_id == conv_id)
            .sort("+timestamp")
            .limit(1)
            .first_or_none()
        )

        return message
    except Exception as e:
        print("Unexpected error occured in mongo function getting first message as:", e)
        return None


async def get_last_20_messages(conversation_id: str):
    try:
        conv_id = PydanticObjectId(conversation_id)

        messages = (
            await Messages.find(Messages.conversation_id == conv_id)
            .sort("-timestamp")
            .limit(20)
            .to_list()
        )

        # Return in chronological order
        return list(reversed(messages))

    except Exception as e:
        print(
            "Unexpected error occurred in mongo function getting last 20 messages as:",
            e,
        )
        return None


async def get_message_by_message_id(message_id: str):
    try:
        message_doc = await Messages.find_one(
            Messages.message_id == PydanticObjectId(message_id)
        )
        return message_doc

    except Exception as e:
        print(
            f"Unexpected error occurred in mongo function getting message by message_id: {e}"
        )
        return None
