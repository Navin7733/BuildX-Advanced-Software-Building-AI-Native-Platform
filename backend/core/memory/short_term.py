"""
Short Term Memory (Redis)
Stores current conversation context and active agent states.
"""
import json
import logging
import redis
from django.conf import settings

logger = logging.getLogger(__name__)

class ShortTermMemory:
    def __init__(self, project_id: str, run_id: str):
        self.project_id = project_id
        self.run_id = run_id
        self.redis = redis.from_url(settings.REDIS_URL)
        self.prefix = f"stm:{project_id}:{run_id}:"
        self.ttl = 60 * 60 * 24  # 24 hours

    def set(self, key: str, value: dict):
        self.redis.setex(
            f"{self.prefix}{key}",
            self.ttl,
            json.dumps(value)
        )

    def get(self, key: str) -> dict | None:
        data = self.redis.get(f"{self.prefix}{key}")
        if data:
            return json.loads(data)
        return None
        
    def append_to_list(self, list_key: str, value: dict):
        full_key = f"{self.prefix}{list_key}"
        self.redis.rpush(full_key, json.dumps(value))
        self.redis.expire(full_key, self.ttl)
        
    def get_list(self, list_key: str) -> list[dict]:
        full_key = f"{self.prefix}{list_key}"
        items = self.redis.lrange(full_key, 0, -1)
        return [json.loads(item) for item in items]
