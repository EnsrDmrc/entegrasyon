import asyncio
import sys
import os

# Ayar
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from services.repricing import run_n11_repricing

async def main():
    print("Test başlatılıyor...", flush=True)
    await run_n11_repricing()
    print("Test bitti.", flush=True)

if __name__ == "__main__":
    asyncio.run(main())
