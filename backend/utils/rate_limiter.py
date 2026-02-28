import asyncio
import time


class TokenBucketLimiter:
    """Simple token bucket rate limiter for async operations."""

    def __init__(self, rate: float, capacity: int = None):
        """
        Args:
            rate: tokens per second
            capacity: max burst capacity (defaults to rate)
        """
        self.rate = rate
        self.capacity = capacity or int(rate)
        self.tokens = self.capacity
        self.last_refill = time.monotonic()
        self._lock = asyncio.Lock()

    async def acquire(self):
        async with self._lock:
            now = time.monotonic()
            elapsed = now - self.last_refill
            self.tokens = min(self.capacity, self.tokens + elapsed * self.rate)
            self.last_refill = now

            if self.tokens < 1:
                wait_time = (1 - self.tokens) / self.rate
                await asyncio.sleep(wait_time)
                self.tokens = 0
            else:
                self.tokens -= 1


# Pre-configured limiters
autocomplete_limiter = TokenBucketLimiter(rate=0.5, capacity=3)  # 30/min
trends_limiter = TokenBucketLimiter(rate=0.17, capacity=2)  # ~10/min
serp_limiter = TokenBucketLimiter(rate=0.17, capacity=2)
competitor_limiter = TokenBucketLimiter(rate=0.08, capacity=1)  # ~5/min
