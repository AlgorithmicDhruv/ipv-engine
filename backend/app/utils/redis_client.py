import os
import json
import logging
import redis

logger = logging.getLogger(__name__)

_client = None


def get_redis_client() -> redis.Redis:
    global _client
    if _client is None:
        url = os.environ.get("REDIS_URL", "redis://localhost:6379/0")
        _client = redis.from_url(url, decode_responses=True)
    return _client


def publish_price(ticker: str, price: float, source: str, price_date: str) -> None:
    client = get_redis_client()
    payload = json.dumps({
        "ticker": ticker,
        "price": price,
        "source": source,
        "price_date": price_date
    })
    client.lpush(f"prices:{ticker}", payload)
    client.expire(f"prices:{ticker}", 86400)  # 24-hour TTL
    logger.info("Published price for %s from %s: %.6f", ticker, source, price)


def consume_prices(ticker: str, count: int = 100) -> list[dict]:
    client = get_redis_client()
    raw_records = client.lrange(f"prices:{ticker}", 0, count - 1)
    results = []
    for raw in raw_records:
        try:
            results.append(json.loads(raw))
        except json.JSONDecodeError:
            logger.warning("Malformed price record in Redis for ticker %s: %s", ticker, raw)
    return results


def get_all_price_keys() -> list[str]:
    client = get_redis_client()
    return client.keys("prices:*")
