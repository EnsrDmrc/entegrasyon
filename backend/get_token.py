import asyncio
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy.future import select

from core.config import settings
from models.user import User
from core.security import create_access_token

async def get_token():
    engine = create_async_engine(settings.ASYNC_DATABASE_URI)
    async_session = sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)
    
    async with async_session() as db:
        result = await db.execute(select(User))
        user = result.scalars().first()
        if user:
            token = create_access_token(subject=str(user.id))
            print("Token:", token)
            
            import urllib.request
            import json
            import urllib.error
            
            data = json.dumps({
                "marketplace_name": "shopify",
                "store_url": "test.myshopify.com",
                "api_key": "shpat_test",
                "is_active": True
            }).encode('utf-8')
            
            req = urllib.request.Request(
                'http://localhost:8000/api/v1/integrations/', 
                data=data, 
                headers={'Content-Type': 'application/json', 'Authorization': f'Bearer {token}'}
            )
            
            try:
                with urllib.request.urlopen(req) as response:
                    print("Status:", response.getcode())
                    print("Response:", response.read().decode('utf-8'))
            except urllib.error.HTTPError as e:
                print("Error Status:", e.code)
                print("Error Body:", e.read().decode('utf-8'))
            
        else:
            print("No users found")

if __name__ == "__main__":
    asyncio.run(get_token())
