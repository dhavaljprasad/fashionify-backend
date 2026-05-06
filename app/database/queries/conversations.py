from app.database.init import Conversations


async def init_new_conversation_document(user_id: str):
    try:
        new_conversation_doc = Conversations(user_id=user_id)
        await new_conversation_doc.insert()
        return new_conversation_doc
    except Exception as e:
        print("Unexpected error occured init new conversation document as:", e)
        return None
