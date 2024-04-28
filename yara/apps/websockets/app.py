from yara.apps.websockets.routers import router
from yara.core.apps import YaraApp
from yara.core.routers import YaraApiRouter


class WebsocketsApp(YaraApp):
    def get_routers(self) -> list[YaraApiRouter]:
        return [router]
