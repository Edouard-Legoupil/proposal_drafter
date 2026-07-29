import asyncio
import logging
import os
import time
from typing import Any

import redis  # type: ignore[import-untyped]
from redis.exceptions import RedisError  # type: ignore[import-untyped]

# This module is responsible for setting up the connection to Redis.
# It includes a fallback mechanism to an in-memory dictionary for local
# development or when Redis is unavailable.

logger = logging.getLogger(__name__)
redis_available = False


def create_redis_client(redis_url: str) -> Any:
    """Create a Redis client from the deployment-provided connection URL."""
    return redis.Redis.from_url(redis_url, decode_responses=True)


try:
    # Attempt to connect to the Redis server.
    # `decode_responses=True` ensures that data read from Redis is automatically
    # decoded from bytes to UTF-8 strings.
    redis_client: Any = create_redis_client(os.getenv("REDIS_URL", "redis://redis:6379/0"))

    # `ping()` checks if the connection to Redis is alive.
    redis_client.ping()
    redis_available = True
    logger.info("Successfully connected to Redis")

except RedisError:
    # If Redis is not available, print a warning and use a fallback storage.
    logger.warning("Could not connect to Redis. Using local in-memory storage fallback.")

    class DictStorage:
        """
        An in-memory dictionary-based storage that mimics the basic
        functionality of the Redis client (`setex`, `get`, `delete`).
        This is used as a fallback for local development when Redis is not running.
        """

        def __init__(self):
            self.storage = {}
            self.expires_at = {}

        def setex(self, key, ttl, value):
            """Set a key with a time-to-live."""
            self.storage[key] = value
            self.expires_at[key] = time.monotonic() + ttl

        def set(self, key, value):
            """Sets a key-value pair."""
            self.storage[key] = value
            self.expires_at.pop(key, None)

        def get(self, key):
            """Gets a value by key."""
            expires_at = self.expires_at.get(key)
            if expires_at is not None and expires_at <= time.monotonic():
                self.delete(key)
                return None
            return self.storage.get(key)

        def delete(self, key):
            """Deletes a key."""
            self.storage.pop(key, None)
            self.expires_at.pop(key, None)

        def publish(self, channel, message):
            """Mock publish method. Does nothing in DictStorage."""
            pass

        def pubsub(self):
            """Mock pubsub method. Returns a mock pubsub object."""
            return self.MockPubSub()

        class MockPubSub:
            async def subscribe(self, channel):
                pass

            async def get_message(self, ignore_subscribe_messages=True, timeout=0):
                # This mock will not receive messages, so it returns None
                await asyncio.sleep(timeout if timeout else 0)
                return None

            async def unsubscribe(self, channel):
                pass

            async def close(self):
                pass

    # Instantiate the fallback storage.
    redis_client = DictStorage()


def is_redis_available() -> bool:
    """Return whether the application is connected to the shared Redis service."""
    return redis_available
