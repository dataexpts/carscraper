from playwright.async_api import Playwright, async_playwright
import asyncio
import re
import time
import json
from datetime import datetime
import safe_scrape as ss
import random
import logging
import uuid

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)
current_datetime = datetime.now()
timestamp = current_datetime.strftime('%Y%m%d')

urls = [
    'https://www.q84sale.com/en/listing/x-series-19503491',
    'https://www.q84sale.com/en/listing/bmw-x5-xdrive-40i-2022-19503326',
    'https://www.q84sale.com/en/listing/g-class-19478514'
]



car_details = []

async def run(playwright: Playwright, url: str):
    browser = await playwright.chromium.launch(headless=False)
    page = await browser.new_page(viewport={"width": 1600, "height": 900},
                                user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) Gecko/20100101 Firefox/132.0',
                                locale='en-US',
                                timezone_id='America/New_York',
                                geolocation={'longitude': -74.006, 'latitude': 40.7128},
                                permissions=['geolocation'])
    
    await page.goto(url=url,  timeout=60000, wait_until='load')

    await page.wait_for_selector('p.text-4-regular.m-text-5-regular.text-neutral_600')
    get_desc = page.locator('p.text-4-regular.m-text-5-regular.text-neutral_600')
    await get_desc.wait_for(state='visible', timeout=30000)
    car_desc = await get_desc.text_content()

    await page.wait_for_selector('button.btn.btn-prim_4sale_500.btn.btn-startIcon', state='visible', timeout=7000)
    get_phone_button = page.locator('button.btn.btn-prim_4sale_500.btn.btn-startIcon')
    await get_phone_button.wait_for(state='visible', timeout=30000)
    await get_phone_button.click()

    await page.wait_for_selector('.d-flex.align-items-center.bg-neutral_50.styles_attr__BN3w_', state='visible', timeout=7000)
    car_specs = await page.query_selector_all('.d-flex.align-items-center.bg-neutral_50.styles_attr__BN3w_')

    car_specs_dict = {}

    time.sleep(1)
    try:
        phone_no = await page.query_selector('div.styles_phoneText__LmLHj.text-4-med.m-text-4-med.text-neutral_900')
        phone_no = await phone_no.text_content()

        for item in car_specs:
            img = await item.query_selector('img')
            alt_text = await img.get_attribute('alt') if img else None

            # Extract text content
            text_div = await item.query_selector('.text-4-med')
            text_content = await text_div.text_content() if text_div else None

            car_specs_dict[alt_text.strip().lower().replace(' ', '_')] = text_content.strip().lower()

        #print(car_specs_dict)
    except Exception as e:
        phone_no = None
    finally:
        internal_details = {
        'phone_no': phone_no,
        'car_desc':car_desc,
        'car_specs':car_specs_dict

    }
        car_details.append(internal_details)

    await browser.close()
    return car_details


async def main():
    # Use async_playwright to manage the Playwright instance
    try:
            async with async_playwright() as playwright:
                for url in urls:
                    result = await run(playwright, url=url)
                        #print(result)
                        #print(result[1])
                    print(result)
    except Exception as e:
        logger.error(e, exc_info=True)

if __name__ == "__main__":
    # Run the async main function using asyncio
    asyncio.run(main())
    