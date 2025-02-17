from playwright.async_api import Playwright, async_playwright
import asyncio
import random
import safe_scrape as ss
import time
import logging
import json


user_agents = [
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Safari/605.1.15',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Edge/120.0.0.0',
    'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
]

user_agent = random.choice(user_agents)
playwright = async_playwright()


### internal page motorgy
url = 'https://www.motorgy.com/en/car-details/dodge-charger-%D8%9Crt/47968'

async def run(url):
    async with async_playwright() as playwright:
        browser = await playwright.chromium.launch(headless=False)
        context = await browser.new_context(viewport={"width": 1600, "height": 900},
                user_agent=user_agent,
                locale='en-US',
                timezone_id='America/New_York'
            )
        page = await context.new_page()
        await page.goto(url, timeout=60000, wait_until='load')
        
        car_dict = {}

        
        try:
            await page.wait_for_selector('.data-table__row', state='visible', timeout=30000)
            
            data_table = await page.query_selector_all('.data-table__row')
            
            # Check if data_table is actually empty
            if not data_table:
                print("No data table rows found")
                await browser.close()
                return car_dict
            
            for items in data_table:
                # Use .text_content() instead of .get_attribute()
                title = await items.query_selector('p')
                item = await items.query_selector('span')
                
                # Check if both elements exist before accessing their text
                if title and item:
                    title_text = await title.text_content()
                    item_text = await item.text_content()
                    
                    # Clean up the text (remove extra whitespace)
                    title_text = title_text.strip().lower().replace(' ', '_')
                    item_text = item_text.strip().lower()
                    
                    # Only add non-empty entries
                    if title_text and item_text:
                        car_dict[title_text] = item_text
            
            print(car_dict)
        
        except Exception as e:
            print(f"An error occurred: {e}")
        
        finally:
            await browser.close()

asyncio.run(run(url))