from yara.apps.orm.commands import downgrade, migrate
from yara.core.apps import YaraApp


class ORMApp(YaraApp):
    commands = (downgrade, migrate)
