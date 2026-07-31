from enum import StrEnum  # Python 3.11+. On older Python, use: class X(str, Enum)
from beanie import Document, PydanticObjectId
from pydantic import Field, BaseModel
from datetime import datetime, timezone
from typing import Optional

# ----------------------------
# ENUMS
# ----------------------------


class CategoryEnum(StrEnum):
    TOP = "top"
    BOTTOM = "bottom"
    DRESS = "dress"
    OUTERWEAR = "outerwear"
    INNERWEAR = "innerwear"
    SLEEPWEAR = "sleepwear"
    ACTIVEWEAR = "activewear"
    ETHNIC_WEAR = "ethnic_wear"


class PatternEnum(StrEnum):
    SOLID = "solid"
    STRIPED = "striped"
    CHECKED = "checked"
    PLAID = "plaid"
    FLORAL = "floral"
    POLKA_DOT = "polka_dot"
    PRINTED = "printed"
    ABSTRACT = "abstract"
    ANIMAL_PRINT = "animal_print"
    CAMOUFLAGE = "camouflage"
    GEOMETRIC = "geometric"
    TIE_DYE = "tie_dye"
    EMBROIDERED = "embroidered"
    LACE = "lace"
    SEQUINNED = "sequinned"
    OMBRE = "ombre"
    COLOR_BLOCK = "color_block"
    PAISLEY = "paisley"
    TEXTURED = "textured"


class FitEnum(StrEnum):
    SLIM = "slim"
    REGULAR = "regular"
    RELAXED = "relaxed"
    OVERSIZED = "oversized"
    SKINNY = "skinny"
    STRAIGHT = "straight"
    BODYCON = "bodycon"
    LOOSE = "loose"
    TAILORED = "tailored"
    ATHLETIC = "athletic"
    CROPPED = "cropped"


class NecklineEnum(StrEnum):
    NOT_APPLICABLE = "not_applicable"
    CREW = "crew"
    V_NECK = "v_neck"
    POLO = "polo"
    HENLEY = "henley"
    BOAT = "boat"
    SCOOP = "scoop"
    SQUARE = "square"
    MOCK = "mock"
    TURTLENECK = "turtleneck"
    HOODED = "hooded"
    COLLARED = "collared"
    OTHER = "other"
    UNKNOWN = "unknown"


class SleeveLengthEnum(StrEnum):
    NOT_APPLICABLE = "not_applicable"
    SLEEVELESS = "sleeveless"
    CAP = "cap"
    SHORT = "short"
    THREE_QUARTER = "three_quarter"
    LONG = "long"
    UNKNOWN = "unknown"


class ClosureEnum(StrEnum):
    NOT_APPLICABLE = "not_applicable"
    UNKNOWN = "unknown"
    BUTTONS = "buttons"
    ZIPPER = "zipper"
    HALF_ZIP = "half_zip"
    DRAWSTRING = "drawstring"
    ELASTIC = "elastic"
    PULLOVER = "pullover"
    HOOK = "hook"
    OTHER = "other"


class SeasonEnum(StrEnum):
    SUMMER = "summer"
    WINTER = "winter"
    MONSOON = "monsoon"
    SPRING = "spring"
    AUTUMN = "autumn"
    ALL_SEASON = "all_season"


class LengthEnum(StrEnum):
    NOT_APPLICABLE = "not_applicable"  # for tops/accessories where length doesn't apply
    MINI = "mini"
    KNEE_LENGTH = "knee_length"
    MIDI = "midi"
    MAXI = "maxi"
    ANKLE_LENGTH = "ankle_length"
    FLOOR_LENGTH = "floor_length"
    CROPPED = "cropped"
    REGULAR = "regular"


class LayeringRoleEnum(StrEnum):
    BASE_LAYER = "base_layer"
    MID_LAYER = "mid_layer"
    OUTER_LAYER = "outer_layer"
    STANDALONE = "standalone"


# ----------------------------
# MODELS
# ----------------------------


class ImagesDict(BaseModel):
    original_image: str = ""
    processed_image: str = ""


class GraphicDict(BaseModel):
    present: bool
    type_graphic: str


class Metadata(BaseModel):
    category: CategoryEnum
    sub_category: list[str]
    colors: list[str]
    pattern: PatternEnum
    graphic: GraphicDict
    fabric: list[str]
    fit: FitEnum
    neckline: NecklineEnum
    sleeve_length: SleeveLengthEnum
    closure: ClosureEnum
    garment_features: list[str]
    season: list[SeasonEnum]
    occasion: list[str]
    style_tags: list[str]
    layering_role: list[LayeringRoleEnum]
    length: LengthEnum
    semantic_summary: str


class WardrobeItems(Document):
    user_id: str = ""
    model_id: Optional[str] = None
    item_id: PydanticObjectId = Field(default_factory=PydanticObjectId)
    images: ImagesDict
    item_name: str = ""
    metadata: Metadata
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    last_worn: Optional[datetime] = None

    class Settings:
        name = "wardrobe_items"
