from yara.apps.featureflags.api_router import api_router
from yara.core.apps import YaraApp


class FeatureFlagApp(YaraApp):
    api_router = api_router
