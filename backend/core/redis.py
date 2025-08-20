#  Third-Party Libraries
import redis

# --- Redis Client Initialization ---

# This module is responsible for setting up the connection to Redis.
# It includes a fallback mechanism to an in-memory dictionary for local
# development or when Redis is unavailable.

try:
    # Attempt to connect to the Redis server.
    # `decode_responses=True` ensures that data read from Redis is automatically
    # decoded from bytes to UTF-8 strings.
    redis_client = redis.Redis(host="redis", port=6379, db=0, decode_responses=True)

    # `ping()` checks if the connection to Redis is alive.
    redis_client.ping()
    print("Successfully connected to Redis")

except redis.ConnectionError:
    # If Redis is not available, print a warning and use a fallback storage.
    print("Warning: Could not connect to Redis. Using in-memory storage as fallback.")

    class DictStorage:
        """
        An in-memory dictionary-based storage that mimics the basic
        functionality of the Redis client (`setex`, `get`, `delete`).
        This is used as a fallback for local development when Redis is not running.
        """
        def __init__(self):
            self.storage = {}

        def setex(self, key, ttl, value):
            """Sets a key with a Time-To-Live (TTL), although the TTL is ignored in this mock."""
            self.storage[key] = value

        def set(self, key, value):
            """Sets a key-value pair."""
            self.storage[key] = value

        def get(self, key):
            """Gets a value by key."""
            return self.storage.get(key)

        def delete(self, key):
            """Deletes a key."""
            self.storage.pop(key, None)

    # Instantiate the fallback storage.
    redis_client = DictStorage()
