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


async def update_conversation_title(conversation_id: str, title: str):
    try:
        conversation_doc = await Conversations.find_one(
            Conversations.conversation_id == PydanticObjectId(conversation_id)
        )

        conversation_doc.title = title
        await conversation_doc.save()
        return conversation_doc

    except Exception as e:
        print("Unexpected error occured updating the conversation document as:", e)
        return None


async def get_conversations_by_user_id(user_id: str, limit: int = 20):
    try:
        conversation_docs = await (
            Conversations.find(Conversations.user_id == PydanticObjectId(user_id))
            .sort("-updated_at")
            .limit(limit)
            .to_list()
        )

        return conversation_docs

    except Exception as e:
        print("Unexpected error occured getting all conversations for user as:", e)
        return []
