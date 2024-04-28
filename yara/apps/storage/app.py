from yara.apps.storage.routers import router
from yara.core.apps import YaraApp
from yara.core.routers import YaraApiRouter


class StorageApp(YaraApp):
    def get_routers(self) -> list[YaraApiRouter]:
        return [router]
