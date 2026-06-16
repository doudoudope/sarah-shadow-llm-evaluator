import fakeredis
import pytest

from app.metrics import metrics


@pytest.fixture(autouse=True)
async def fake_redis():
    fake = fakeredis.FakeAsyncRedis()
    original = metrics._redis
    metrics._redis = fake
    yield fake
    await fake.flushall()
    metrics._redis = original
    await fake.aclose()
