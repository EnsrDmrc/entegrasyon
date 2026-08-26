import asyncio
from core.database import AsyncSessionLocal
from sqlalchemy import text

async def check():
    async with AsyncSessionLocal() as session:
        try:
            result = await session.execute(text("SELECT column_name FROM information_schema.columns WHERE table_name='marketplace_integrations';"))
            print(result.fetchall())
        except Exception as e:
            print("Postgres error:", e)
            result = await session.execute(text("PRAGMA table_info(marketplace_integrations);"))
            print(result.fetchall())

asyncio.run(check())
