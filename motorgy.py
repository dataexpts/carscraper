from playwright.async_api import Playwright, async_playwright
import asyncio
import random
import safe_scrape as ss
import time
import logging
import json
import uuid
from datetime import datetime


user_agents = [
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Safari/605.1.15',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Edge/120.0.0.0',
    'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
]

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('motorgy_scrape_log.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

user_agent = random.choice(user_agents)
playwright = async_playwright()
url = 'https://www.motorgy.com/en/used-cars'

current_datetime = datetime.now()
timestamp = current_datetime.strftime('%Y%m%d')

async def check_last_page(page):
    try:
        #print("Finding pagination div...")
        pagination_div = await page.query_selector('#pagingDiv')
        
        if pagination_div:
            #print("Finding last active link...")
            active_links = await page.query_selector_all('a.activeLink')  # Get all active links
            if active_links:
                last_active_link = active_links[-1]  # Get the last one
                #print("Getting href attribute...")
                href = await last_active_link.get_attribute('href')
                
                if href:
                    #print(f"Found href: {href}")
                    # Extract page number from href
                    last_page_number = int(href.split('pn=')[1])
                    #print(f"Last page number: {last_page_number}")
                    
                    # Get current page number
                    current_url = page.url
                    current_page = int(current_url.split('pn=')[1]) if 'pn=' in current_url else 1
                    #print(f"Current page: {current_page}")
                    
                    is_last_page = current_page >= last_page_number
                    #print(f"Is last page: {is_last_page}")
                    
                    return current_page, is_last_page
    
        return 1, False
        
    except Exception as e:
        print(f"Error in check_last_page at position: {str(e)}")
        return 1, False

def to_json_file(data, filename):
    try:
        with open(filename, 'r', encoding='utf-8') as f:
            file_data = json.load(f)
    except:
        file_data = []
    
    file_data.append(data)
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(file_data, f, indent=4)
    return filename

## add logging and debugging
async def run():
    async with async_playwright() as playwright:
        browser = await playwright.chromium.launch(headless=True)
        context = await browser.new_context(viewport={"width": 1600, "height": 900},
                                    user_agent=user_agent,
                                    locale='en-US',
                                    timezone_id='America/New_York'
                                    #geolocation={'longitude': 59.913034295248146, 'latitude':  10.760390096262885},
                                    #permissions=['geolocation']
                                    )
        page = await context.new_page()
        await page.goto(url,  timeout=60000, wait_until='load')

        car_dict = {}
        car_list = []
        #two_word_brands = ['Land Rover', 'Aston Martin', 'Alfa Romeo', 'Great Wall']
        # Land Rover, Aston Martin, Alfa Romeo, Great Wall
        cars_scraped = 0
        while True:
            await page.wait_for_selector('.card-body', state='visible', timeout=30000)
            cars = await page.query_selector_all('.card-body')
            #next_button =  page.locator('#pagingDiv a.disableLink[href*="pn="]')
            next_button = await page.locator('a:has-text("»"):last-child').element_handle()
            current_page, last_page = await check_last_page(page)

            

            logger.info("Found %d cars on page %d ", len(cars), current_page)

            

            for car in cars:
                card_title_check = await car.query_selector('.card-title')
                
                # these are nested tags
                price_containers = await car.query_selector_all('.d-flex.justify-content-between')
                #print(price_containers)

                if price_containers:
                    last_container = price_containers[-1]
                    price_span = await last_container.query_selector('.color_title.ff-semiBold.fs-16')
                    
                    if price_span:
                        price_text = await price_span.inner_text()
                        #prices.append(price_text)
                        #print(price_text)

                if card_title_check:
                    name = await card_title_check.query_selector('.ff-semiBold.fs-16.color_title')
                    link = await name.get_attribute('href')
                    name = await name.text_content()
                    split_names = name.split('؜')
                    brand = split_names[0]
                    model = ''.join(split_names[1:]) #split_names[1]
                    year = await car.query_selector('.feature-cars-year.me-2.ff-semiBold.fs-12.color_title')
                    year = await year.text_content()
                    mileage = await car.query_selector('.feature-cars-KM.ff-semiBold.me-2.fs-12.color_subtitle')
                    mileage = await mileage.text_content()
                

                    car_dict ={
                    'uuid': str(uuid.uuid4()),
                    'url': link,
                    'brand': brand.strip().replace('-', ' '),
                    'page':current_page,
                    'timestamp': timestamp,
                    'model': model.strip().replace('-', ' '),
                    'year': year,
                    'mileage':mileage.strip().replace(',', '').split()[0],
                    'color':None,
                    'price': price_text.replace(',', '').split()[0]
                    }
                    #print(name)
                    car_list.append(car_dict)
            if last_page:
                break
            else:
                #print(str(await next_button.count()))
                #await next_button.scroll_into_view_if_needed()
                cars_scraped += len(cars)   
                logger.info('total cars scraped: %d', cars_scraped)
                time.sleep(random.uniform(1.5,2.5))

                x,y = ss.random_mouse_movement()
                await page.mouse.move(x, y)
                await page.wait_for_timeout(random.randint(300, 800))
                await next_button.scroll_into_view_if_needed()
                delay = ss.random_delay(1.5,3)

                await page.wait_for_timeout(delay * 1000)
                await next_button.click()
                #print(await response.status)
                continue
           

    to_json_file(car_list, 'car_list_motorgy.json')
    await browser.close()
    logging.info('Scraping motorgy done. Check output file')
    #print(car_list)


            
asyncio.run(run())

