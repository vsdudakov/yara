from yara.apps.featureflags.api_router import api_router
from yara.core.api_router import YaraApiRouter
from yara.core.apps import YaraApp


class FeatureFlagApp(YaraApp):
    def get_api_router(self) -> YaraApiRouter:
        return api_router
