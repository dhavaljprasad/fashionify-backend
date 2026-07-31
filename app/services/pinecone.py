from pinecone import Pinecone
from app.config.variables import ConfigVariables
from app.ai.openai import client
import json

pc = Pinecone(api_key=ConfigVariables.PINECONE_API_KEY)
wardrobe_index = pc.Index(ConfigVariables.PINECONE_INDEX_NAME)


async def embed_text(text: str) -> list[float]:
    res = client.embeddings.create(model="text-embedding-3-large", input=text)
    return res.data[0].embedding


def build_embedding_text(metadata: dict) -> str:
    return f"""
        Category: {metadata["category"]}

        Sub-category:
        {", ".join(metadata["sub_category"])}

        Colors:
        {", ".join(metadata["colors"])}

        Pattern:
        {metadata["pattern"]}

        Graphic:
        {json.dumps(metadata["graphic"])}

        Fabric:
        {", ".join(metadata["fabric"])}

        Fit:
        {metadata["fit"]}

        Neckline:
        {metadata["neckline"]}

        Sleeve Length:
        {metadata["sleeve_length"]}

        Garment Features:
        {", ".join(metadata["garment_features"])}

        Season:
        {", ".join(metadata["season"])}

        Occasion:
        {", ".join(metadata["occasion"])}

        Style:
        {", ".join(metadata["style_tags"])}

        Layering Role:
        {", ".join(metadata["layering_role"])}

        Length:
        {metadata["length"]}

        Description:
        {metadata["semantic_summary"]}
    """.strip()


def build_pinecone_metadata(metadata: dict) -> dict:
    return {
        "primary_category": metadata["category"],
        "sub_category": metadata["sub_category"],
        "season": metadata["season"],
        "layering_role": metadata["layering_role"],
    }


async def upsert_wardrobe_item(
    metadata: dict,
    item_id: str,
    user_id: str,
):
    try:
        text_to_embed = build_embedding_text(metadata)
        embedding = await embed_text(text_to_embed)

        pinecone_metadata = {
            "user_id": user_id,
            "item_id": item_id,
            **build_pinecone_metadata(metadata),
        }

        wardrobe_index.upsert(
            vectors=[
                {
                    "id": item_id,
                    "values": embedding,
                    "metadata": pinecone_metadata,
                }
            ]
        )

        return True

    except Exception as e:
        print(f"Error inserting wardrobe item into Pinecone: {e}")
        return False


async def delete_wardrobe_item_pinecone(
    user_id: str,
    item_id: str,
):
    try:
        wardrobe_index.delete(
            filter={
                "user_id": {"$eq": user_id},
                "item_id": {"$eq": item_id},
            }
        )
        return True

    except Exception as e:
        print(f"Error deleting wardrobe item from Pinecone: {e}")
        return False
