import abc
import typing as tp

from yara.settings import YaraSettings


class MemoryBackend:
    settings: YaraSettings

    def __init__(
        self,
        settings: YaraSettings,
    ) -> None:
        self.settings = settings

    @abc.abstractmethod
    async def up(self) -> None:
        ...

    @abc.abstractmethod
    async def healthcheck(self) -> bool:
        ...

    @abc.abstractmethod
    async def shutdown(self) -> None:
        ...

    @abc.abstractmethod
    async def sadd(self, queue_name: str, *values: tp.Any) -> int:
        ...

    @abc.abstractmethod
    async def srem(self, queue_name: str, *values: tp.Any) -> int:
        ...

    @abc.abstractmethod
    async def smembers(self, name: str) -> set[str]:
        ...

    @abc.abstractmethod
    async def sismember(self, name: str, value: str) -> bool:
        ...

    @abc.abstractmethod
    async def set(self, key: str, value: tp.Any) -> str:
        ...

    @abc.abstractmethod
    async def get(self, key: str) -> str | None:
        ...

    @abc.abstractmethod
    async def delete(self, key: str) -> int:
        ...

    @abc.abstractmethod
    async def exists(self, key: str) -> int:
        ...

    @abc.abstractmethod
    async def expire(self, key: str, time: int) -> int:
        ...

    @abc.abstractmethod
    async def lpush(self, queue_name: str, *args: tp.Any) -> int:
        ...

    @abc.abstractmethod
    async def rpop(self, queue_name: str, count: int | None = None) -> str | list[str] | None:
        ...

    @abc.abstractmethod
    async def brpop(self, queue_names: list[str], timeout: int | None = 0) -> list[str]:
        ...
