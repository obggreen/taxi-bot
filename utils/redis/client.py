from typing import Union

from redis.asyncio import Redis


class RedisClient:
    def __init__(self, redis_url: str):
        self.redis_url = redis_url
        self.client: Redis = None

    async def initialize(self) -> 'RedisClient':
        self.client = Redis.from_url(self.redis_url, encoding="utf-8", decode_responses=True)
        return self

    async def get(self, key: str):
        return await self.client.get(key)

    async def set(self, key: str, value: Union[int, str], ex: int = None) -> bool:
        return await self.client.set(key, value, ex=ex)

    async def ttl(self, key: str):
        return await self.client.ttl(key)

    async def pttl(self, key: str):
        return await self.client.pttl(key)

    async def delete(self, key: str) -> int:
        return await self.client.delete(key)

    async def close(self) -> None:
        await self.client.close()
