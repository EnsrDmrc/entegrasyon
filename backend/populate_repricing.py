import asyncio
import sys
import os
import logging
logging.basicConfig(level=logging.INFO)

sys.path.append('./backend')

from services.repricing import run_n11_repricing

if __name__ == "__main__":
    print("Starting manual repricing data gather...")
    asyncio.run(run_n11_repricing())
    print("Finished.")
