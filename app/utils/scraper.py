from playwright.async_api import async_playwright


async def extract_table_data(table_locator):
    """
    Converts a table into:
    [
        ["Size", "Chest"],
        ["S", "38"],
        ["M", "40"]
    ]
    """

    rows_data = []

    try:
        rows = await table_locator.locator("tr").all()

        for row in rows:
            cells = await row.locator("th, td").all()

            row_data = []

            for cell in cells:
                text = (await cell.inner_text()).strip()

                if text:
                    row_data.append(text)

            if row_data:
                rows_data.append(row_data)

    except Exception:
        pass

    return rows_data if rows_data else None


async def scrape_amazon(page):

    product_type = None
    product_image = None
    product_size = None

    # Product Type from <title>
    try:
        product_type = await page.title()
    except Exception:
        pass

    # Product Image from #landingImage
    try:
        image = page.locator("#landingImage")

        if await image.count():
            product_image = await image.get_attribute(
                "src"
            ) or await image.get_attribute("data-old-hires")
    except Exception:
        pass

    # Size Table (Optional)
    try:
        size_table = page.locator("#fit-sizechartv2-0-table-0")

        if await size_table.count():
            product_size = await extract_table_data(size_table)
    except Exception:
        pass

    return {
        "product_type": product_type,
        "product_image": product_image,
        "product_size": product_size,
    }


async def scrape_flipkart(page):

    product_type = None
    product_image = None
    product_size = None

    # Product Type from <title>
    try:
        product_type = await page.title()
    except Exception:
        pass

    # Product Image from og:image
    try:
        meta_image = page.locator('meta[property="og:image"]')

        if await meta_image.count():
            product_image = await meta_image.get_attribute("content")
    except Exception:
        pass

    # First Table (Optional)
    try:
        table = page.locator("table").first

        if await table.count():
            product_size = await extract_table_data(table)
    except Exception:
        pass

    return {
        "product_type": product_type,
        "product_image": product_image,
        "product_size": product_size,
    }


async def scrape_product(link: str):

    async with async_playwright() as p:

        browser = await p.chromium.launch(
            headless=True,
            args=[
                "--no-sandbox",
                "--disable-dev-shm-usage",
            ],
        )

        page = await browser.new_page()

        try:

            await page.goto(
                link,
                wait_until="domcontentloaded",
                timeout=60000,
            )

            # Small buffer for lazy-loaded content
            await page.wait_for_timeout(2000)

            if "amazon." in link or "amzn." in link:
                result = await scrape_amazon(page)

            elif "flipkart." in link:
                result = await scrape_flipkart(page)

            else:
                raise ValueError(f"Unsupported website: {link}")

            return result

        finally:
            await browser.close()
