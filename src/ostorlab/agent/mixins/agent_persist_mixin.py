"""Mixin to enable distributed storage for a group of agent replicas or for a single agent that needs reliable storage.

A typical use-case is ensuring that a message value is processed only once in case multiple other agent are producing
duplicates or similar ones.

Typical usage:

```python
    status_agent = agent_persist_mixin.AgentPersistMixin(agent_settings)
    status_agent.set_add('crawler_agent_asset_dna', dna)
    is_new = not status_agent.set_is_member()
```
"""
from typing import Dict, List, Set
import redis

from ostorlab.runtimes import definitions as runtime_definitions


class AgentPersistMixin:
    """Agent mixin to persist data. The mixin enables distributed storage of a group of agent replicas or for a single
     agent that needs reliable storage."""

    def __init__(self, agent_settings: runtime_definitions.AgentSettings) -> None:
        """Initializes the mixin from the agent settings.

        Args:
            agent_settings: Agent runtime settings.
        """
        if agent_settings.redis_url is None:
            raise ValueError('agent settings is missing redis url')
        self._redis_client = redis.Redis.from_url(agent_settings.redis_url)

    def set_add(self, key: str, *value: List) -> bool:
        """Helper function that takes care of reporting if the specified DNA has been tested in the past, or mark it
        as tested.
        The method can be used to sync multiple agents that may encounter the same test input but need to test it
        only once.
        Storage is shared between agents, ensure the keys used are unique.

        Args:
            key: Set key.
            value: List of values to add to set.

        Returns:
            True if it is a new member, False otherwise.
        """
        return bool(self._redis_client.sadd(key, *value))

    def set_is_member(self, key: str, value: str) -> bool:
        """Indicates whether value is member of the set identified by key.

        Args:
            key: The set key.
            value: The value to check.

        Returns:
            True if it is a member, False otherwise.
        """
        return self._redis_client.sismember(key, value)

    def set_len(self, key: str) -> int:
        """Helper function that returns the set cardinality (number of elements) of the set stored at key.
        The method can be used to sync multiple agents that may receive test inputs but need to test
        less than X test inputs.
        Storage is shared between agents, ensure the keys used are unique.

        Args:
            key: Set key.

        Returns:
            The cardinality (number of elements) of the set, or 0 if key does not exist.
        """
        return self._redis_client.scard(key)

    def set_members(self, key: str) -> Set:
        """Helper function that returns all the members of the set value stored at key.

        Args:
            key: Set key.

        Returns:
             The value of key, or empty set when key does not exist.
        """
        return self._redis_client.smembers(key)

    def add(self, key: str, value) -> bool:
        """Helper function that Set key to hold the string value.

        Args:
            key: Key.
            value: String value.

        Returns:
            Status of the set command.
        """
        return self._redis_client.set(key, value)

    def get(self, key: str) -> bytes:
        """Get the value of key. If the key does not exist None is returned.

        Args:
            key: Key.

        Returns:
            Value of key, or None when key does not exist.
        """
        return self._redis_client.get(key)

    def hash_add(self, hash_name: str, mapping: Dict) -> bool:
        """Set mapping within hash hash_name. If hash_name does not exist a new hash is created.
        If key exists, value is overriden.

        Args:
            hash_name: Name of the hash.
            mapping: Dict of key/value pairs that will be hadded to hash_name

        Returns:
            True if the key does not exist, False otherwise
        """
        return bool(self._redis_client.hset(name=hash_name, mapping=mapping))

    def hash_exists(self, hash_name: str, key: str)-> bool:
        """Returns a boolean indicating if key exists within hash hash_name.

        Args:
            hash_name: Name of the hash.
            key: Key in the hash.

        Returns:
            True if the key exists in the hash.
        """
        return self._redis_client.hexists(hash_name, key)

    def hash_get(self, hash_name: str, key: str):
        """Return the value of key within the hash hash_name.

        Args:
            hash_name: Name of the hash.
            key: Key in the hash.

        Returns:
            Value of the key stored in hash_name, None if the key does not exist.
        """
        return self._redis_client.hget(hash_name, key)

    def hash_get_all(self, hash_name: str)-> Dict:
        """Returns a dict of the hash’s name/value pairs.

        Args:
            hash_name: Name of the hash.

        Returns:
            Dict of the hash’s name/value pairs.
        """
        return self._redis_client.hgetall(hash_name)

    def delete(self: str, key) -> bool:
        """Delete a specific key.

        Args:
            key: Key.

        Returns:
            True if the key is delete, False otherwise.
        """
        return bool(self._redis_client.delete(key))

    def value_type(self, key:str)-> str:
        """Return a string representation of the type of the value stored at key.

        Args:
            key: Key.

        Returns:
            String representation of the type of value stored at key. eg: set, string.
        """
        return self._redis_client.type(key).decode()
