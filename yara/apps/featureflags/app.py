from yara.apps.featureflags.api_router import feature_flags_router
from yara.core.apps import YaraApp


class FeatureFlagApp(YaraApp):
    api_router = feature_flags_router
