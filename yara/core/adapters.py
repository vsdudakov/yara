import typing as tp
from abc import abstractmethod


class YaraAdapter:
    root_app: tp.Any

    def __init__(self, root_app: tp.Any) -> None:
        self.root_app = root_app

    @abstractmethod
    async def up(self) -> None:
        """
        Start the app.
        """
        ...

    @abstractmethod
    async def healthcheck(self) -> bool:
        """
        Check if the app is healthy.
        """
        ...

    @abstractmethod
    async def shutdown(self) -> None:
        """
        Shutdown the app.
        """
        ...
