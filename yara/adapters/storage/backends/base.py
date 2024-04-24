import abc
import typing as tp

from yara.settings import YaraSettings


class StorageBackend:
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
    async def send_email(self, template_id: str, to: str, payload: dict[str, tp.Any]) -> None:
        ...

    @abc.abstractmethod
    async def presigned_get_object(self, bucket_name: str, object_name: str) -> str | None:
        ...

    @abc.abstractmethod
    async def presigned_put_object(self, bucket_name: str, object_name: str) -> str | None:
        ...

    @abc.abstractmethod
    async def remove_object(self, bucket_name: str, object_name: str) -> None:
        ...

    @abc.abstractmethod
    async def remove_objects(self, bucket_name: str, object_names: list[str]) -> None:
        ...
