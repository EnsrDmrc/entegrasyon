import asyncio
import asyncpg

async def setup_db():
    print("Veritabanına bağlanılıyor...")
    try:
        conn = await asyncpg.connect(user='postgres', password='ensarbaba123', host='localhost', port=5432, database='postgres')
        exists = await conn.fetchval("SELECT 1 FROM pg_database WHERE datname = 'entegrasyon_db'")
        if not exists:
            await conn.execute('CREATE DATABASE entegrasyon_db')
            print("Veritabanı 'entegrasyon_db' başarıyla oluşturuldu!")
        else:
            print("Veritabanı 'entegrasyon_db' zaten mevcut.")
        await conn.close()
    except Exception as e:
        print(f"BAĞLANTI HATASI: {e}")

asyncio.run(setup_db())
