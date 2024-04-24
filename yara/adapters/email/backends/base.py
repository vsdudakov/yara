import abc
import typing as tp

from yara.settings import YaraSettings


class EmailBackend:
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
    async def send_email(self, to: str, template_id: str, payload: dict[str, tp.Any]) -> None:
        ...
