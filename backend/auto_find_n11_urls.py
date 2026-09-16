import asyncio
import sys
import json
import logging
from curl_cffi import requests
from bs4 import BeautifulSoup

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

sys.path.append('./backend')
from core.database import AsyncSessionLocal
from sqlalchemy.future import select
from models.product import Product
import urllib.parse

async def find_urls():
    logger.info("Starting N11 URL finder...")
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
    }
    
    async with AsyncSessionLocal() as db:
        result = await db.execute(select(Product).where(Product.n11_url == None))
        products = result.scalars().all()
        
        logger.info(f"Found {len(products)} products without N11 URL.")
        
        for p in products:
            search_query = p.sku
            if not search_query:
                continue
                
            encoded_q = urllib.parse.quote(search_query)
            search_url = f"https://www.n11.com/arama?q={encoded_q}"
            logger.info(f"Searching for {p.sku}: {search_url}")
            
            try:
                # Synchronous request because curl_cffi requests doesn't support async well easily without AsyncSession
                resp = requests.get(search_url, headers=headers, impersonate="chrome110", timeout=10.0)
                if resp.status_code == 200:
                    soup = BeautifulSoup(resp.text, 'lxml')
                    found_url = None
                    for script in soup.find_all('script'):
                        if script.string and 'window.model = ' in script.string:
                            raw = script.string.strip()
                            start = raw.find('window.model = ') + len('window.model = ')
                            jstr = raw[start:]
                            if jstr.endswith(';'): jstr = jstr[:-1]
                            data = json.loads(jstr)
                            
                            results = data.get('searchResults', [])
                            if results and len(results) > 0:
                                # Get the exact product page URL of the first result
                                first_item = results[0]
                                url = first_item.get('url') or first_item.get('productUrl')
                                if url:
                                    found_url = url
                                    break
                    
                    if found_url:
                        logger.info(f"-> Found URL for {p.sku}: {found_url}")
                        p.n11_url = found_url
                        db.add(p)
                    else:
                        logger.warning(f"-> No results found for {p.sku} on N11.")
            except Exception as e:
                logger.error(f"Error searching for {p.sku}: {e}")
                
            # Sleep briefly to avoid getting blocked
            await asyncio.sleep(1)
            
        await db.commit()
    logger.info("Finished N11 URL finder.")

if __name__ == "__main__":
    asyncio.run(find_urls())
