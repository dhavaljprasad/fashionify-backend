from beanie import Document, PydanticObjectId
from pydantic import Field


class ComparisonAnalytics(Document):
    comparison_id: PydanticObjectId = Field(default_factory=PydanticObjectId)
    user_id: str = ""
    searched_url: str = ""
    compared_stores: list[str] = []
    success: bool = False
    lowest_price: int = 0
    heighest_price: int = 0

    class Settings:
        name = "comparison_analytics"
