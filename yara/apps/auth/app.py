from yara.apps.auth.api_router import auth_router
from yara.apps.auth.commands import create_group_moderator, create_superuser
from yara.core.apps import YaraApp


class AuthApp(YaraApp):
    commands = (create_superuser, create_group_moderator)
    api_router = auth_router
