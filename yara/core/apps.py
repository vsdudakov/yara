import typing as tp

from yara.core.api_router import YaraApiRouter
from yara.core.middlewares import YaraMiddleware


class YaraApp:
    api_router: YaraApiRouter | None = None
    middlewares: list[tuple[type[YaraMiddleware], dict[str, tp.Any]]] | None = None
    commands: tp.Any | None = None
    settings: list[tuple[str, str, bool, tp.Any]] | None = None

    root_app: tp.Any

    def __init__(self, root_app: tp.Any) -> None:
        self.root_app = root_app
