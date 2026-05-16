from app.database.init import Conversations
from app.database.models.conversations import EntryType
from beanie import PydanticObjectId


async def init_new_conversation_document(user_id: str):
    try:
        new_conversation_doc = Conversations(user_id=user_id)
        await new_conversation_doc.insert()
        return new_conversation_doc
    except Exception as e:
        print("Unexpected error occured init new conversation document as:", e)
        return None


async def update_conversation_type(conversation_id: str, conversation_type: EntryType):
    try:
        conversation_doc = await Conversations.find_one(
            Conversations.conversation_id == PydanticObjectId(conversation_id)
        )

        conversation_doc.entry_type = conversation_type

        await conversation_doc.save()

        return conversation_doc

    except Exception as e:
        print("Unexpected error occured updating the conversation document as:", e)
        return None
