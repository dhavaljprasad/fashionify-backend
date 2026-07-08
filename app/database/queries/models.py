from app.database.models import Models
from app.database.models.models import MaleMeasurements, FemaleMeasurements
from beanie import PydanticObjectId
import traceback


def _to_int(value):
    if value in (None, ""):
        return 0
    return int(float(value))


def _to_float(value):
    if value in (None, ""):
        return 0.0
    return float(value)


def _normalize_measurements(gender: str, measurements):
    if hasattr(measurements, "model_dump"):
        payload = measurements.model_dump()
    elif isinstance(measurements, dict):
        payload = measurements
    else:
        payload = dict(measurements)

    if gender == "male":
        return MaleMeasurements(
            height=_to_int(payload.get("height")),
            body_type=str(payload.get("body_type", "")).strip(),
            shoulder_width=_to_float(payload.get("shoulder_width")),
            chest=_to_float(payload.get("chest")),
            waist=_to_float(payload.get("waist")),
            belly=_to_float(payload.get("belly")),
            hips=_to_float(payload.get("hips")),
            pant_waist=_to_float(payload.get("pant_waist")),
            thigh=_to_float(payload.get("thigh")),
        )

    if gender == "female":
        return FemaleMeasurements(
            height=_to_int(payload.get("height")),
            body_shape=str(payload.get("body_shape", "")).strip(),
            shoulder_width=_to_float(payload.get("shoulder_width")),
            bust=_to_float(payload.get("bust")),
            underbust=_to_float(payload.get("underbust")),
            waist=_to_float(payload.get("waist")),
            hips=_to_float(payload.get("hips")),
            pant_waist=_to_float(payload.get("pant_waist")),
            thigh=_to_float(payload.get("thigh")),
        )

    return measurements


async def init_new_model_document(
    user_id: str,
    gender: str,
    image: str,
    model_name: str,
    measurements: MaleMeasurements | FemaleMeasurements | dict,
):
    try:
        normalized_measurements = _normalize_measurements(gender, measurements)

        if gender == "male":
            new_model_doc = Models(
                user_id=user_id,
                gender=gender,
                image=image,
                model_name=model_name,
                male_measurements=normalized_measurements,
            )
        elif gender == "female":
            new_model_doc = Models(
                user_id=user_id,
                gender=gender,
                image=image,
                model_name=model_name,
                female_measurements=normalized_measurements,
            )
        await new_model_doc.insert()
        return new_model_doc
    except Exception as e:
        print("Unexpected error occured init new model document as:", e)
        traceback.print_exc()
        return None


async def get_user_model_documents(user_id: str):
    try:
        model_docs = await Models.find(Models.user_id == str(user_id)).to_list()
        return model_docs
    except Exception as e:
        print("Unexpected error occured getting all user models as:", e)
        traceback.print_exc()
        return []


async def get_model_document_by_id(model_id: str):
    try:
        model_doc = await Models.find_one(Models.model_id == PydanticObjectId(model_id))
        return model_doc
    except Exception as e:
        print("Unexpected error occured getting model document by id as:", e)
        traceback.print_exc()
        return None
