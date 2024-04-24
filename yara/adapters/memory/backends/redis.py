import logging
import typing as tp

import redis.asyncio as redis

from yara.adapters.memory.backends.base import MemoryBackend

logger = logging.getLogger(__name__)


class RedisMemoryBackend(MemoryBackend):
    client: tp.Any | None

    def __init__(self, settings: tp.Any) -> None:
        super().__init__(settings)
        self.client = None

    async def up(self) -> None:
        pool = redis.BlockingConnectionPool.from_url(
            self.dsn,
            max_connections=self.max_connections,
            timeout=self.timeout,
        )
        self.client = redis.Redis.from_pool(pool)

    async def healthcheck(self) -> bool:
        if not self.client:
            return False
        try:
            return await self.client.ping()
        except redis.ConnectionError:
            logger.warning("RedisMemoryBackend is not healthy")
            return False

    async def shutdown(self) -> None:
        if self.client:
            await self.client.aclose(close_connection_pool=True)
            self.client = None

    async def sadd(self, queue_name: str, *values: tp.Any) -> int:
        if not self.client:
            raise ValueError("RedisMemoryBackend is not connected")
        return await self.client.sadd(queue_name, *values)

    async def srem(self, queue_name: str, *values: tp.Any) -> int:
        if not self.client:
            raise ValueError("RedisMemoryBackend is not connected")
        return await self.client.srem(queue_name, *values)

    async def smembers(self, name: str) -> set[str]:
        if not self.client:
            raise ValueError("RedisMemoryBackend is not connected")
        return await self.client.smembers(name)

    async def sismember(self, name: str, value: str) -> bool:
        if not self.client:
            raise ValueError("RedisMemoryBackend is not connected")
        return bool(await self.client.sismember(name, value))

    async def set(self, key: str, value: tp.Any) -> str:
        if not self.client:
            raise ValueError("RedisMemoryBackend is not connected")
        return await self.client.set(key, value)

    async def get(self, key: str) -> str | None:
        if not self.client:
            raise ValueError("RedisMemoryBackend is not connected")
        return await self.client.get(key)

    async def delete(self, key: str) -> int:
        if not self.client:
            raise ValueError("RedisMemoryBackend is not connected")
        return await self.client.delete(key)

    async def exists(self, key: str) -> int:
        if not self.client:
            raise ValueError("RedisMemoryBackend is not connected")
        return await self.client.exists(key)

    async def expire(self, key: str, time: int) -> int:
        if not self.client:
            raise ValueError("RedisMemoryBackend is not connected")
        return await self.client.expire(key, time)

    async def lpush(self, queue_name: str, *args: tp.Any) -> int:
        if not self.client:
            raise ValueError("RedisMemoryBackend is not connected")
        return await self.client.lpush(queue_name, *args)

    async def rpop(self, queue_name: str, count: int | None = None) -> str | list[str] | None:
        if not self.client:
            raise ValueError("RedisMemoryBackend is not connected")
        return await self.client.rpop(queue_name, count=count)

    async def brpop(self, queue_names: list[str], timeout: int | None = 0) -> list[str]:
        if not self.client:
            raise ValueError("RedisMemoryBackend is not connected")
        return await self.client.brpop(queue_names, timeout=timeout)
