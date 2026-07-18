from pydantic import BaseModel
from playwright.async_api import async_playwright
from app.config.variables import ConfigVariables


class ScraperData(BaseModel):
    image_url: str | None
    product_card: str | None
    comparison_table: str | None
    recommendation: str | None
    price_history: str | None


async def scrape_price_comparison(link: str) -> ScraperData:

    async with async_playwright() as p:

        browser = await p.chromium.launch(
            headless=True,
            args=[
                "--no-sandbox",
                "--disable-dev-shm-usage",
            ],
        )

        page = await browser.new_page()

        magic_link = f"{ConfigVariables.MAGIC_LINK}{link}"

        try:

            await page.goto(
                magic_link,
                wait_until="domcontentloaded",
                timeout=60000,
            )

            await page.wait_for_timeout(3000)

            async def clean_outer_html(locator):
                try:

                    if not await locator.count():
                        return None

                    return await locator.first.evaluate("""
(el) => {

    const clone = el.cloneNode(true);

    //----------------------------------------------------------------------
    // Remove unwanted attributes
    //----------------------------------------------------------------------

    const REMOVE_ATTRS = [
        "class",
        "style",
        "id",
        "role",
        "tabindex",
        "loading",
        "decoding",
        "fetchpriority"
    ];

    clone.querySelectorAll("*").forEach(node => {

        REMOVE_ATTRS.forEach(attr => node.removeAttribute(attr));

        [...node.attributes].forEach(attr => {

            const name = attr.name.toLowerCase();

            if (
                name.startsWith("data-") ||
                name.startsWith("aria-") ||
                name.startsWith("on")
            ) {
                node.removeAttribute(attr.name);
            }

        });

    });

    //----------------------------------------------------------------------
    // Remove useless tags
    //----------------------------------------------------------------------

    [
        "script",
        "style",
        "svg",
        "path",
        "defs",
        "symbol",
        "use",
        "noscript"
    ].forEach(tag => {

        clone.querySelectorAll(tag).forEach(node => node.remove());

    });

    //----------------------------------------------------------------------
    // Remove comments
    //----------------------------------------------------------------------

    const walker = document.createTreeWalker(
        clone,
        NodeFilter.SHOW_COMMENT
    );

    const comments = [];

    while (walker.nextNode()) {
        comments.push(walker.currentNode);
    }

    comments.forEach(node => node.remove());

    //----------------------------------------------------------------------
    // Unwrap useless layout divs
    //----------------------------------------------------------------------

    let changed = true;

    while (changed) {

        changed = false;

        clone.querySelectorAll("div").forEach(div => {

            if (
                div.attributes.length === 0 &&
                div.children.length === 1 &&
                div.firstElementChild &&
                div.textContent.trim() === div.firstElementChild.textContent.trim()
            ) {

                div.replaceWith(div.firstElementChild);
                changed = true;

            }

        });

    }

    //----------------------------------------------------------------------
    // Remove empty elements
    //----------------------------------------------------------------------

    clone.querySelectorAll("*").forEach(node => {

        if (
            node.children.length === 0 &&
            node.textContent.trim() === "" &&
            !["img", "br"].includes(node.tagName.toLowerCase())
        ) {
            node.remove();
        }

    });

    //----------------------------------------------------------------------
    // Normalize whitespace
    //----------------------------------------------------------------------

    clone.innerHTML = clone.innerHTML
        .replace(/>\\s+</g, "><")
        .replace(/\\s{2,}/g, " ")
        .trim();

    return clone.outerHTML;

}
                    """)

                except:
                    return None

            # ---------------------------------------------------------------
            # Product Image
            # ---------------------------------------------------------------

            image_url = await clean_outer_html(page.locator("img.product_image"))

            # ---------------------------------------------------------------
            # Product Card
            # ---------------------------------------------------------------

            product_card = None

            try:

                heading = page.locator("h1").first

                if await heading.count():

                    product_card = await heading.evaluate("""
(el) => {

    let node = el;

    for (let i = 0; i < 6; i++) {

        if (!node.parentElement)
            break;

        node = node.parentElement;

    }

    return node;

}
                    """)

                    product_card = await clean_outer_html(
                        page.locator("h1").locator("xpath=ancestor::*[6]")
                    )

            except:
                pass

            # ---------------------------------------------------------------
            # Comparison Table
            # ---------------------------------------------------------------

            comparison_table = None

            try:

                compare_heading = page.get_by_text(
                    "Compare",
                    exact=False,
                ).first

                if await compare_heading.count():

                    comparison_table = await clean_outer_html(
                        compare_heading.locator("xpath=ancestor::section[1]")
                    )

            except:
                pass

            # ---------------------------------------------------------------
            # Recommendation
            # ---------------------------------------------------------------

            recommendation = None

            try:

                recommendation_heading = page.get_by_text(
                    "Our Recommendation",
                    exact=False,
                ).first

                if await recommendation_heading.count():

                    recommendation = await clean_outer_html(
                        recommendation_heading.locator("xpath=ancestor::section[1]")
                    )

            except:
                pass

            # ---------------------------------------------------------------
            # Price History
            # ---------------------------------------------------------------

            price_history = None

            try:

                history = page.get_by_text(
                    "Price History",
                    exact=False,
                ).first

                if not await history.count():

                    history = page.get_by_text(
                        "Lowest Price",
                        exact=False,
                    ).first

                if await history.count():

                    price_history = await clean_outer_html(
                        history.locator("xpath=ancestor::section[1]")
                    )

            except:
                pass

            return ScraperData(
                image_url=image_url,
                product_card=product_card,
                comparison_table=comparison_table,
                recommendation=recommendation,
                price_history=price_history,
            )

        finally:
            await browser.close()
