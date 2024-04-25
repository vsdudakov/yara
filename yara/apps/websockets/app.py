from yara.apps.websockets.api_routers import api_router
from yara.core.api_routers import YaraApiRouter
from yara.core.apps import YaraApp


class WebsocketsApp(YaraApp):
    def get_api_routers(self) -> list[YaraApiRouter]:
        return [api_router]
