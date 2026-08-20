import contextlib
import redis.asyncio as redis
from core.config import settings

redis_client = redis.from_url(settings.REDIS_URL, decode_responses=True)

@contextlib.asynccontextmanager
async def distributed_lock(lock_name: str, timeout: int = 10, sleep_time: float = 0.1):
    """
    Redis tabanlı Dağıtık Kilit (Distributed Lock) mekanizması.
    Aynı anda gelen siparişlerde 'over-selling' (fazla satış) problemini çözer.
    """
    import asyncio
    import time
    
    lock_key = f"lock:{lock_name}"
    acquired = False
    
    end_time = time.time() + timeout
    try:
        while time.time() < end_time:
            # setnx (Set if Not eXists)
            acquired = await redis_client.set(lock_key, "locked", nx=True, ex=timeout)
            if acquired:
                break
            await asyncio.sleep(sleep_time)
            
        if not acquired:
            raise TimeoutError(f"Could not acquire lock for {lock_name} within {timeout} seconds.")
            
        yield
    finally:
        if acquired:
            await redis_client.delete(lock_key)
