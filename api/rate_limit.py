import time
from core.broker import RedisBroker

class SlidingWindowLimiter:
    def __init__(self, limit: int = 10, window: int = 60):
        self.broker = RedisBroker()
        self.limit = limit
        self.window = window

    def is_allowed(self, identifier: str) -> bool:
        r = self.broker.conn
        key = f"rate_limit_sliding:{identifier}"
        now = time.time()
        expiry_limit = now - self.window

        try:
            pipe = r.pipeline()
            # 1. Remove timestamps older than our window
            pipe.zremrangebyscore(key, 0, expiry_limit)
            # 2. Add current request timestamp
            pipe.zadd(key, {str(now): now})
            # 3. Count remaining timestamps in the set
            pipe.zcard(key)
            # 4. Set expiration on the whole set to save memory
            pipe.expire(key, self.window)
            
            results = pipe.execute()
            current_count = results[2] # result of zcard

            return current_count <= self.limit
            
        except Exception as e:
            print(f"Limiter Error: {e}")
            return True # Fail open

limiter = SlidingWindowLimiter(limit=100, window=60)