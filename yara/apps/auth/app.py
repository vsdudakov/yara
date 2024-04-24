import typing as tp

from yara.apps.auth.api_router import api_router
from yara.apps.auth.commands import create_group_moderator, create_superuser
from yara.core.api_router import YaraApiRouter
from yara.core.apps import YaraApp


class AuthApp(YaraApp):
    def get_api_router(self) -> YaraApiRouter:
        return api_router

    def get_commands(self) -> list[tp.Any]:
        return [create_superuser, create_group_moderator]
