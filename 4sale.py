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

# Setup logging to both file and console

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('scrape_log.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)
current_datetime = datetime.now()
timestamp = current_datetime.strftime('%Y%m%d')

#url = 'https://www.q84sale.com/en/automotive/cars/1/lincoln?c=1752'

'''
    'chevrolet': 'https://www.q84sale.com/en/automotive/cars/1/chevrolet?c=109',
    'ford': 'https://www.q84sale.com/en/automotive/cars/1/ford?c=110',
    'geely': 'https://www.q84sale.com/en/automotive/cars/1/geely?c=2029',
    'chery' : 'https://www.q84sale.com/en/automotive/cars/1/chery?c=2960',
    'bmw' : 'https://www.q84sale.com/en/automotive/cars/1/bmw?c=114',
    'land rover' : 'https://www.q84sale.com/en/automotive/cars/1/land-rover?c=132',
    'mercedes' : 'https://www.q84sale.com/en/automotive/cars/1/mercedes?c=113',
    'kia' : 'https://www.q84sale.com/en/automotive/cars/1/kia?c=523',
    'hyundai' : 'https://www.q84sale.com/en/automotive/cars/1/hyundai?c=120',
    'honda' : 'https://www.q84sale.com/en/automotive/cars/1/honda?c=117',
    'toyota' : 'https://www.q84sale.com/en/automotive/cars/1/toyota?c=138',
'nissan' : 'https://www.q84sale.com/en/automotive/cars/1/nissan?c=116',
'lexus' : 'https://www.q84sale.com/en/automotive/cars/1/lexus?c=119',
'gmc' : 'https://www.q84sale.com/en/automotive/cars/1/gmc?c=111',
'porsche' : 'https://www.q84sale.com/en/automotive/cars/1/porsche?c=115',
'volkswagen' : 'https://www.q84sale.com/en/automotive/cars/1/volkswagen-?c=521',
'jeep' : 'https://www.q84sale.com/en/automotive/cars/1/jeep?c=519',
'dodge' : 'https://www.q84sale.com/en/automotive/cars/1/dodge?c=108',
'mg' : 'https://www.q84sale.com/en/automotive/cars/1/mg?c=2774',

'cadillac' : 'https://www.q84sale.com/en/automotive/cars/1/cadillac?c=520',
'infiniti':'https://www.q84sale.com/en/automotive/cars/1/infiniti-?c=524',
'audi':'https://www.q84sale.com/en/automotive/cars/1/audi?c=112'
'''

cars_dict = {
            'cadillac' : 'https://www.q84sale.com/en/automotive/cars/1/cadillac?c=520',
'infiniti':'https://www.q84sale.com/en/automotive/cars/1/infiniti-?c=524'
            }

user_agents = [
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Safari/605.1.15',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Edge/120.0.0.0',
    'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
]

user_agent = random.choice(user_agents)

def extract_number(text):
    try:
        if text is None:
            return None
        else:
        # Split and take first part, replace comma with dot
            cleaned = text.replace(',', '').split()[0]
            return float(cleaned)
    except (ValueError, IndexError):
        return None

def is_two_digits(number):
    try:
        if number is None:
            return None
        else:
            abs_num = abs(number)
            # Check if between 100 and 999
            return 10 <= abs_num <= 100
    except (ValueError, IndexError):
        return None



def mileage_processor(mileage):
    if mileage is None:
        return False, None
    
    # First try to match number followed by standalone 'k'
    k_pattern = r'(\d+(?:\.\d+)?)\s*\b[kK]\b'
    k_match = re.search(k_pattern, mileage)
    
    if k_match:
        return 'k', float(k_match.group(1))
    
    # If no 'k' match, try to match number followed by 'km'
    km_pattern = r'(\d+(?:\.\d+)?)\s*(?:km|KM|Km|kM)'
    km_match = re.search(km_pattern, mileage)
    
    if km_match:
        return 'km', float(km_match.group(1))
    
    # If no 'k' or 'km' match, try to match just a number
    number_pattern = r'^\s*(\d+(?:\.\d+)?)\s*$'
    number_match = re.search(number_pattern, mileage)
    
    if number_match:
        return False, float(number_match.group(1))
    
    return False, None

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


async def check_last_page(page):
    try:
        # Wait for any version of the next button to be present
        await page.wait_for_selector('[data-test="type_next"]', timeout=5000)
        
        # Check specifically for disabled state
        disabled_next = page.locator('[data-test="type_next"].styles_disabled__O4kp4')
        enabled_next = page.locator('[data-test="type_next"]:not(.styles_disabled__O4kp4)')
        
        # If disabled exists and enabled doesn't
        is_disabled = await disabled_next.count() > 0
        is_enabled = await enabled_next.count() > 0
        
        return is_disabled and not is_enabled
        
    except Exception as e:
        print(f"Error during last page check: {e}")
        logger.error('Error during last page check: str(%s)', exc_info=True)
        return False


async def run(playwright: Playwright, url: str, brand: str):
    browser = await playwright.chromium.launch(headless=False)
    context = await browser.new_context(viewport={"width": 1600, "height": 900},
                                user_agent=user_agent,
                                locale='en-US',
                                timezone_id='America/New_York'
                                #geolocation={'longitude': 59.913034295248146, 'latitude':  10.760390096262885},
                                #permissions=['geolocation']
                                )
    page = await context.new_page()
    #await context.clear_permissions()
    #await context.clear_cookies()

    
    await page.goto(url,  timeout=60000, wait_until='load')
    
    car_list = []
    page_num = 1
    
    logger.info("\nScraping page %d - %s", page_num, page.url)
    #print(f"\nScraping page {page_num} - {page.url}")
    
    # Process cars on current page
    #for brand, url in cars_dict.items():
    cars_scraped = 0
    while True:
        await page.wait_for_selector('.StackedCard_card__Kvggc', state='visible', timeout=30000)
        cars = await page.query_selector_all('.StackedCard_card__Kvggc')

        
        logger.info("Found %d cars on page %d for brand %s", len(cars), page_num, brand)
        #print(f"Found {len(cars)} cars on page {page_num} for brand {brand}")


        for car in cars:
            
            model = await car.query_selector('.text-6-med.text-neutral_600')
            model = await model.text_content() if model else "NA"

            car_properties = await car.query_selector('.styles_attr___ur_q')
            car_properties = await car_properties.text_content() if car_properties else 'NA'

            price = await car.query_selector('.h6.text-prim_4sale_500')
            price = await price.text_content() if price else 'NA'

            link = await car.get_attribute('href')
            
            if len(car_properties.split(',')) > 1 and len(car_properties.split(',')) < 4:
                has_k, mileage_proc = mileage_processor(car_properties.split(',')[1].strip().replace(',', ''))
            elif len(car_properties.split(',')) == 4:
                has_k, mileage_proc = mileage_processor(car_properties.split(',')[1].strip().replace(',', '') + car_properties.split(',')[2].strip().replace(',', ''))
            else:
                continue
            
            year_text = car_properties.split(',')[0].strip()
            year_value = 1970 if year_text == 'Before 1980' else year_text

            if has_k == 'k' or (has_k == 'km' and len(str(mileage_proc)) == 4  
                                                    and datetime.now().year - int(year_value) > 0):
                mileage = mileage_proc * 1000
            elif has_k == 'k' or (has_k == 'km' and int(mileage_proc)/1000 < 1000
                                                    and datetime.now().year - int(year_value) > 0):
                mileage = mileage_proc * 100
            else:
                mileage = None
                #mileage = mileage.split(',')[1].strip().replace(',', '')

            current_datetime = datetime.now()
            timestamp = current_datetime.strftime('%Y-%m-%d %H:%M:%S')

            if is_two_digits(extract_number(price)) is None:
                price = None
            elif is_two_digits(extract_number(price)):
                price = extract_number(price) * 1000
            else:
                price = extract_number(price)


            if len(car_properties.split(',')) == 3:
                color = car_properties.split(',')[2].strip()
            elif len(car_properties.split(',')) == 2:
                color = car_properties.split(',')[1].strip()
            elif len(car_properties.split(',')) == 1:
                color = None
            else:
                color = car_properties.split(',')[3].strip()
            
            car_info = {
                'uuid': str(uuid.uuid4()),
                'url': link,
                'brand': brand,
                'page': page_num,
                'timestamp': timestamp,
                'model': model.strip(),
                'year': year_value, #year.split(',')[0].strip(),
                'mileage': mileage,
                'color': color,#car_properties.split(',')[2].strip(),
                'price': price #extract_number(price) #extract_number(price) * 1000 if isinstance(extract_number(price), float) else extract_number(price)
            }
            car_list.append(car_info)
            
        cars_scraped += len(cars)   
        logger.info('total cars scraped: %d', cars_scraped)
        next_button = page.locator('a[data-test="type_next"]:not(.styles_disabled__O4kp4)')
        
        time.sleep(random.uniform(1.5,2.5))

        x,y = ss.random_mouse_movement()
        await page.mouse.move(x, y)
        await page.wait_for_timeout(random.randint(300, 800))

        print(str(await next_button.count()))
        
        if await check_last_page(page):
            print("Reached final page")
            break
        else: 
            if await next_button.count() > 0:
                await next_button.wait_for(state='visible', timeout=5000)
            else:
                break

            x,y = ss.random_mouse_movement()
            await page.mouse.move(x, y)
            await page.wait_for_timeout(random.randint(300, 800))

            await next_button.scroll_into_view_if_needed()
            
            delay = ss.random_delay(1.5,3)

            await page.wait_for_timeout(delay * 1000)
            await next_button.click()
            
            page_num += 1

    to_json_file(car_list, 'car_list3.json')
    await browser.close() 
    return car_list


async def main():
    # Use async_playwright to manage the Playwright instance
    try:
        async with async_playwright() as playwright:
            for brand, url in cars_dict.items():
                result = await run(playwright, url=url, brand=brand)
                #print(result)
                to_json_file(result, 'car_list_'+brand+'_'+str(timestamp)+'.json')
                logger.info('Finished scraping for %s', brand)
    except Exception as e:
        logger.error(e, exc_info=True)

if __name__ == "__main__":
    # Run the async main function using asyncio
    asyncio.run(main())
    #insert.bulk_import_cars('car_list.json')
