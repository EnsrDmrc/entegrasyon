import asyncio
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from services.n11_scraper import N11Scraper

async def run():
    engine = create_async_engine('postgresql+asyncpg://postgres:ensarbaba123@localhost:5432/entegrasyon_db')
    async with AsyncSession(engine) as session:
        result = await session.execute(text("SELECT n11_url FROM products WHERE sku='3M1300'"))
        row = result.fetchone()
        
    if row and row[0]:
        url = row[0]
        print('URL:', url)
        scraper = N11Scraper()
        comps = scraper.get_competitors(url)
        print('Scraped competitors:')
        for idx, c in enumerate(comps):
            print(f"{idx}. {c['seller_name']} - {c['price']}")
    else:
        print('URL not found in DB')

if __name__ == "__main__":
    asyncio.run(run())
