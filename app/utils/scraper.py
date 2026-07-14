from playwright.async_api import async_playwright


async def extract_table_data(size_locator):
    """
    Converts a size table/container into:
    [
        ["Size", "Chest"],
        ["S", "38"],
        ["M", "40"]
    ]
    """

    rows_data = []

    try:
        table = size_locator
        nested_table = size_locator.locator("table").first

        if await nested_table.count():
            table = nested_table

        rows = await table.locator("tr").all()

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

    if rows_data:
        return rows_data

    try:
        text = (await size_locator.inner_text()).strip()

        for line in text.splitlines():
            row_data = [cell.strip() for cell in line.split("\t") if cell.strip()]

            if not row_data and line.strip():
                row_data = [line.strip()]

            if row_data:
                rows_data.append(row_data)

    except Exception:
        pass

    return rows_data if rows_data else None


async def get_product_title(page):
    try:
        return await page.title()
    except Exception:
        return None


async def get_meta_content(page, selectors):
    for selector in selectors:
        try:
            meta = page.locator(selector).first

            if await meta.count():
                content = await meta.get_attribute("content")

                if content:
                    return content
        except Exception:
            pass

    return None


async def get_size_data(page, selector, index=0):
    try:
        locator = page.locator(selector).nth(index)

        if await locator.count():
            return await extract_table_data(locator)
    except Exception:
        pass

    return None


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


async def scrape_myntra(page):

    product_type = None
    product_image = None
    product_size = None

    # Product Type from <title>
    try:
        product_type = await page.title()
    except Exception:
        pass

    # Product Image from itemprop="image"
    try:
        meta_image = page.locator('meta[itemprop="image"]')

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


async def scrape_naykaa_fashion(page):

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


async def scrape_og_image_brand(page, size_selector="table", table_index=0):

    return {
        "product_type": await get_product_title(page),
        "product_image": await get_meta_content(
            page,
            [
                'meta[property="og:image"]',
                'meta[name="og:image"]',
            ],
        ),
        "product_size": await get_size_data(page, size_selector, table_index),
    }


async def scrape_the_souled_store(page):

    return {
        "product_type": await get_product_title(page),
        "product_image": await get_meta_content(
            page,
            [
                'meta#ogimage[property="og:image"]',
                'meta[property="og:image"][name="og:image"]',
                'meta[property="og:image"]',
                'meta[name="og:image"]',
            ],
        ),
        "product_size": await get_size_data(page, "div.size-wrap"),
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

            normalized_link = link.lower()

            if "amazon." in normalized_link or "amzn." in normalized_link:
                result = await scrape_amazon(page)

            elif "flipkart." in normalized_link:
                result = await scrape_flipkart(page)

            elif "myntra." in normalized_link:
                result = await scrape_myntra(page)

            elif "nykaafashion." in normalized_link:
                result = await scrape_naykaa_fashion(page)

            elif "wforwoman." in normalized_link:
                result = await scrape_og_image_brand(page)

            elif "shopforaurelia." in normalized_link:
                result = await scrape_og_image_brand(page, table_index=1)

            elif "wishfulbyw." in normalized_link:
                result = await scrape_og_image_brand(page)

            elif "elleven." in normalized_link:
                result = await scrape_og_image_brand(page)

            elif "biba." in normalized_link:
                result = await scrape_og_image_brand(page, "div.size-table table")

            elif "thesouledstore." in normalized_link:
                result = await scrape_the_souled_store(page)

            elif "savana." in normalized_link:
                result = await scrape_og_image_brand(page)

            else:
                raise ValueError(f"Unsupported website: {link}")

            return result

        finally:
            await browser.close()
