import typing as tp

from yara.adapters.memory.backends.base import MemoryBackend
from yara.core.adapters import YaraAdapter
from yara.core.helpers import import_class
from yara.main import YaraBaseRootApp


class MemoryAdapter(YaraAdapter):
    backend: MemoryBackend
    root_app: YaraBaseRootApp

    def __init__(self, root_app: YaraBaseRootApp) -> None:
        super().__init__(root_app)
        backend_cls_path: str | None = getattr(self.root_app.settings, "YARA_MEMORY_BACKEND", None)

        if not backend_cls_path:
            raise ValueError("Provide YARA_MEMORY_BACKEND settings")

        backend_cls: type[MemoryBackend] | None = import_class(backend_cls_path)
        if not backend_cls:
            raise ValueError(f"Backend {backend_cls_path} not found")

        self.backend = backend_cls(self.root_app.settings)

    async def up(self) -> None:
        await self.backend.up()

    async def healthcheck(self) -> bool:
        return await self.backend.healthcheck()

    async def shutdown(self) -> None:
        await self.backend.shutdown()

    async def sadd(self, queue_name: str, *values: tp.Any) -> int:
        return await self.backend.sadd(queue_name, *values)

    async def srem(self, queue_name: str, *values: tp.Any) -> int:
        return await self.backend.srem(queue_name, *values)

    async def smembers(self, name: str) -> set[str]:
        return await self.backend.smembers(name)

    async def sismember(self, name: str, value: str) -> bool:
        return await self.backend.sismember(name, value)

    async def set(self, key: str, value: tp.Any) -> str:
        return await self.backend.set(key, value)

    async def get(self, key: str) -> str | None:
        return await self.backend.get(key)

    async def delete(self, key: str) -> int:
        return await self.backend.delete(key)

    async def exists(self, key: str) -> int:
        return await self.backend.exists(key)

    async def expire(self, key: str, time: int) -> int:
        return await self.backend.expire(key, time)

    async def lpush(self, queue_name: str, *args: tp.Any) -> int:
        return await self.backend.lpush(queue_name, *args)

    async def rpop(self, queue_name: str, count: int | None = None) -> str | list[str] | None:
        return await self.backend.rpop(queue_name, count=count)

    async def brpop(self, queue_names: list[str], timeout: int | None = 0) -> list[str]:
        return await self.backend.brpop(queue_names, timeout=timeout)
