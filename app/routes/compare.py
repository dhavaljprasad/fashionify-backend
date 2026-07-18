from fastapi import APIRouter, Request
from pydantic import BaseModel
from app.database.queries.pooling import init_pooling_doc
from app.workers.tasks import price_compare

router = APIRouter(prefix="/compare", tags=["compare"])


class PriceCompareRequest(BaseModel):
    product_url: str


@router.post("/")
async def get_price_comparison_function(request: Request, body: PriceCompareRequest):
    try:
        # getting user_id from the request-payload
        user = request.state.user
        user_id = user["id"]

        product_url = body.product_url

        new_pooling_doc = await init_pooling_doc(
            user_id=user_id, pooling_type="comparison"
        )

        price_compare.delay(
            product_url=product_url,
            user_id=user_id,
            pooling_id=str(new_pooling_doc.pooling_id),
        )

        if new_pooling_doc:
            response = {
                "status": "success",
                "pooling_id": str(new_pooling_doc.pooling_id),
            }
            return response
        else:
            response = {"status": "faliure", "pooling_id": ""}
            return response

    except Exception as e:
        print(
            f"Unexpected error occured in router function get_price_comparison_function as {e}"
        )
        return None
