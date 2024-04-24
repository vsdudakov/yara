import typing as tp

from yara.apps.orm.commands import downgrade, migrate
from yara.core.apps import YaraApp


class ORMApp(YaraApp):
    def get_commands(self) -> list[tp.Any]:
        return [downgrade, migrate]
