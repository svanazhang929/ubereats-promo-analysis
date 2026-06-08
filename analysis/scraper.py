import asyncio
import json
import re
from datetime import datetime
from pathlib import Path
from playwright.async_api import async_playwright

SUBURBS = [
    "Sydney CBD",
    "Parramatta", 
    "Newtown",
    "Surry Hills",
    "Chatswood",
]

OUTPUT_PATH = Path("data/raw")


async def set_location(page, suburb: str) -> bool:
    await page.goto("https://www.ubereats.com/au", wait_until="domcontentloaded")
    await page.wait_for_timeout(3000)
    try:
        inputs = await page.query_selector_all("input")
        await inputs[0].click()
        await page.wait_for_timeout(500)
        await page.keyboard.type(suburb + " NSW", delay=80)
        await page.wait_for_timeout(2500)
        suggestions = await page.query_selector_all("[role='option']")
        if suggestions:
            await suggestions[0].click()
            await page.wait_for_timeout(3000)
            print(f"  Location set: {suburb}")
            return True
        return False
    except Exception as e:
        print(f"  Location failed: {e}")
        return False


async def parse_card(card, suburb: str):
    try:
        # Name from h3
        name_el = await card.query_selector("h3")
        name = await name_el.inner_text() if name_el else None
        if not name:
            return None

        # Rating + reviews from aria-label
        rating, review_count = None, None
        rating_el = await card.query_selector("[aria-label*='Rating']")
        if rating_el:
            aria = await rating_el.get_attribute("aria-label")
            m = re.search(r"Rating:\s*([\d.]+)\s*stars?\.\s*([\d,k\+]+)\s*review", aria, re.I)
            if m:
                rating = float(m.group(1))
                review_count = m.group(2).replace(",", "")

        # Delivery fee
        delivery_fee = None
        fee_els = await card.query_selector_all("[aria-label*='delivery']")
        for el in fee_els:
            aria = await el.get_attribute("aria-label") or ""
            if "free delivery" in aria.lower():
                delivery_fee = 0.0
                break
            m = re.search(r"\$([\d.]+)\s*delivery", aria, re.I)
            if m:
                delivery_fee = float(m.group(1))
                break

        # Fallback: scan all text for delivery fee
        if delivery_fee is None:
            full_text = await card.inner_text()
            if re.search(r"free delivery", full_text, re.I):
                delivery_fee = 0.0
            else:
                m = re.search(r"\$([\d.]+)\s*Delivery Fee", full_text, re.I)
                if m:
                    delivery_fee = float(m.group(1))

        # Delivery time + promo from full text
        full_text = await card.inner_text()
        lines = [l.strip() for l in full_text.splitlines() if l.strip()]

        delivery_time_min, delivery_time_max = None, None
        promo_label, promo_type = None, None
        price_tier = None
        is_sponsored = False

        for line in lines:
            # Delivery time
            m = re.search(r"(\d+)[–\-](\d+)\s*min", line)
            if m:
                delivery_time_min = int(m.group(1))
                delivery_time_max = int(m.group(2))

            # Price tier
            if re.fullmatch(r"\${1,4}", line):
                price_tier = len(line)

            # Promo
            if re.search(r"%\s*off|off\s*\$|free item|spend\s*\$|buy\s*\d|\$\d+\s*off", line, re.I):
                if not re.search(r"delivery fee", line, re.I):
                    promo_label = line
                    if "% off" in line.lower():
                        promo_type = "Percentage Discount"
                    elif re.search(r"off\s*\$|\$\d+\s*off", line, re.I):
                        promo_type = "Spend & Save"
                    elif "free item" in line.lower():
                        promo_type = "Free Item"
                    else:
                        promo_type = "Other"

            if re.search(r"sponsored", line, re.I):
                is_sponsored = True

        return {
            "name": name.strip(),
            "suburb": suburb,
            "rating": rating,
            "review_count": review_count,
            "delivery_fee": delivery_fee,
            "delivery_time_min": delivery_time_min,
            "delivery_time_max": delivery_time_max,
            "price_tier": price_tier,
            "promo_label": promo_label,
            "promo_type": promo_type,
            "is_sponsored": is_sponsored,
            "scraped_at": datetime.now().isoformat(),
        }
    except Exception as e:
        return None


async def scrape_suburb(page, suburb: str) -> list:
    print(f"\nScraping: {suburb}")
    success = await set_location(page, suburb)
    if not success:
        return []

    for _ in range(10):
        await page.evaluate("window.scrollBy(0, 800)")
        await page.wait_for_timeout(1200)

    cards = await page.query_selector_all("[data-testid='store-card']")
    print(f"  Found {len(cards)} cards")

    restaurants = []
    seen = set()
    for card in cards:
        parsed = await parse_card(card, suburb)
        if parsed and parsed["name"] not in seen:
            seen.add(parsed["name"])
            restaurants.append(parsed)

    print(f"  Parsed {len(restaurants)} restaurants")
    return restaurants


async def main():
    OUTPUT_PATH.mkdir(parents=True, exist_ok=True)
    all_restaurants = []

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False, slow_mo=80)
        context = await browser.new_context(
            viewport={"width": 1280, "height": 800},
            user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        )
        page = await context.new_page()

        for suburb in SUBURBS:
            try:
                results = await scrape_suburb(page, suburb)
                all_restaurants.extend(results)
            except Exception as e:
                print(f"  Suburb failed ({suburb}): {e}")

        await browser.close()

    output_file = OUTPUT_PATH / f"restaurants_{datetime.now().strftime('%Y%m%d_%H%M')}.jsonl"
    with open(output_file, "w") as f:
        for r in all_restaurants:
            f.write(json.dumps(r) + "\n")

    print(f"\nDone. {len(all_restaurants)} restaurants → {output_file}")


if __name__ == "__main__":
    asyncio.run(main())