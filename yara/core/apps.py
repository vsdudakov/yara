import typing as tp

from yara.core.middlewares import YaraMiddleware
from yara.core.routers import YaraApiRouter


class YaraApp:
    root_app: tp.Any

    def __init__(self, root_app: tp.Any) -> None:
        self.root_app = root_app

    def get_middlewares(self) -> list[tuple[type[YaraMiddleware], dict[str, tp.Any]]]:
        return []

    def get_commands(self) -> list[tp.Any]:
        return []

    def get_routers(self) -> list[YaraApiRouter]:
        return []
