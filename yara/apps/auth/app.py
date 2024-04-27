import typing as tp

from yara.apps.auth.api_routers import api_router
from yara.apps.auth.commands import create_superuser
from yara.core.api_routers import YaraApiRouter
from yara.core.apps import YaraApp


class AuthApp(YaraApp):
    def get_api_routers(self) -> list[YaraApiRouter]:
        return [api_router]

    def get_commands(self) -> list[tp.Any]:
        return [create_superuser]
