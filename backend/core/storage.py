class InMemoryStorage:
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
storage_client = InMemoryStorage()
