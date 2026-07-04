from beanie import Document, PydanticObjectId
from pydantic import BaseModel, Field
from enum import StrEnum


class TypeOfGender(StrEnum):
    MALE = "male"
    FEMALE = "female"


class MaleMeasurements(BaseModel):
    height: int
    body_type: str
    shoulder_width: float
    chest: float
    waist: float
    belly: float
    hips: float
    pant_waist: float
    thigh: float


class FemaleMeasurements(BaseModel):
    height: int
    body_shape: str
    shoulder_width: float
    bust: float
    underbust: float
    waist: float
    hips: float
    pant_waist: float
    thigh: float


class Models(Document):
    user_id: str = ""
    gender: TypeOfGender = TypeOfGender.MALE
    image: str = ""
    model_name: str = ""
    model_id: PydanticObjectId = Field(default_factory=PydanticObjectId)

    male_measurements: MaleMeasurements | None = None
    female_measurements: FemaleMeasurements | None = None

    class Settings:
        name = "models"
