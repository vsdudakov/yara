from yara.apps.websockets.api_router import api_router
from yara.core.apps import YaraApp


class WebsocketsApp(YaraApp):
    api_router = api_router
