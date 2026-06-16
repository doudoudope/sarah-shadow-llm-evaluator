import asyncio


class MetricsStore:
    def __init__(self):
        self._lock = asyncio.Lock()
        self.total = 0
        self.matches = 0
        self.mismatches = 0

    async def record_match(self):
        async with self._lock:
            self.total += 1
            self.matches += 1

    async def record_mismatch(self):
        async with self._lock:
            self.total += 1
            self.mismatches += 1

    @property
    def match_rate(self) -> float:
        if self.total == 0:
            return 0.0
        return round(self.matches / self.total * 100, 2)


metrics = MetricsStore()
