import typing as tp

from yara.apps.auth.commands import create_superuser
from yara.apps.auth.routers import router
from yara.core.apps import YaraApp
from yara.core.routers import YaraApiRouter


class AuthApp(YaraApp):
    def get_routers(self) -> list[YaraApiRouter]:
        return [router]

    def get_commands(self) -> list[tp.Any]:
        return [create_superuser]
