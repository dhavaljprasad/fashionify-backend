import re

from app.database.init import ComparisonAnalytics


def parse_price(price: str | None) -> int:
    if not price:
        return 0
    digits = re.sub(r"[^\d]", "", price)
    return int(digits) if digits else 0


async def save_comparison_analytics(
    user_id: str,
    searched_url: str,
    comparison_result,
) -> bool:
    try:

        compared_stores = list(
            {
                store["brand_name"].strip()
                for store in comparison_result["comparison_table"]
                if store["brand_name"].strip()
            }
        )

        analytics = ComparisonAnalytics(
            user_id=user_id,
            searched_url=searched_url,
            compared_stores=compared_stores,
            success=len(compared_stores) > 0,
            lowest_price=parse_price(comparison_result["lowest_price"]),
            heighest_price=parse_price(comparison_result["highest_price"]),
        )

        await analytics.insert()
        return analytics

    except Exception as e:

        print(f"Failed to save comparison analytics: {e}")

        return False
