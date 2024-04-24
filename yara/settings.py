import os
from collections.abc import Generator

from pydantic_settings import BaseSettings


class YaraSettings(BaseSettings):
    # API
    YARA_PROJECT_NAME: str = "Yara"
    YARA_ENV: str = os.getenv("YARA_ENV", "local")

    # SENTRY
    YARA_SENTRY_DSN: str | None = None
    YARA_SENTRY_TRACES_SAMPLE_RATE: float | None = None

    # CONFIG
    YARA_ADAPTERS: list[str] = [
        "yara.adapters.orm.adapter.ORMAdapter",
        "yara.adapters.memory.adapter.MemoryAdapter",
        "yara.adapters.storage.adapter.StorageAdapter",
        "yara.adapters.email.adapter.EmailAdapter",
        "yara.adapters.oauth.adapter.OAuth2Adapter",
    ]
    YARA_APPS: list[str] = [
        "yara.apps.orm.app.ORMApp",
        "yara.apps.featureflags.app.FeatureFlagApp",
        "yara.apps.auth.app.AuthApp",
    ]

    def get_apps_paths(self) -> Generator[str, None, None]:
        for app in self.YARA_APPS:
            app_path = app.split(".app.")[0]
            yield app_path

    # Celery
    YARA_CELERY_BROKER_URI: str
    YARA_CELERY_RESULT_BACKEND_URI: str

    # Logging
    YARA_LOGGING_LEVEL: str = "INFO"

    # Orm
    YARA_ORM_BACKEND: str = "yara.adapters.orm.backends.postgres.ORMPostgresBackend"
    YARA_ORM_DSN: str
    YARA_ORM_MIGRATIONS_TABLE: str = "yara__orm__migrations"

    # Memory
    YARA_MEMORY_BACKEND: str = "yara.adapters.memory.backends.redis.RedisMemoryBackend"
    YARA_MEMORY_DSN: str
    YARA_MEMORY_MAX_CONNECTIONS: int = 100
    YARA_MEMORY_TIMEOUT: int | None = None

    # Storage
    YARA_STORAGE_BACKEND: str = "yara.adapters.storage.backends.minio.MinioStorageBackend"
    YARA_STORAGE_MINIO_URL: str
    YARA_STORAGE_MINIO_ACCESS_KEY: str
    YARA_STORAGE_MINIO_SECRET_KEY: str

    # Email
    YARA_EMAIL_BACKEND: str = "yara.adapters.email.backends.smtp.SmtpEmailBackend"
    YARA_EMAIL_SMTP_HOST: str
    YARA_EMAIL_TEMPLATES: dict[str, str] = {}
    YARA_EMAIL_SMTP_FROM: str
    YARA_EMAIL_SMTP_PORT: int = 587
    YARA_EMAIL_SMTP_USERNAME: str
    YARA_EMAIL_SMTP_PASSWORD: str
    YARA_EMAIL_SMTP_USE_TLS: bool = True
    YARA_EMAIL_SMTP_TIMEOUT: int | None = None

    # Auth
    YARA_AUTH_SECRET_KEY: str
    YARA_AUTH_EXP_ACCESS_TOKEN: int = 60 * 60
    YARA_AUTH_EXP_REFRESH_TOKEN: int = 60 * 60 * 24 * 7
    YARA_AUTH_EXP_MAGIC_VERIFICATION_TOKEN: int = 60 * 60 * 24
    YARA_AUTH_EXP_SIGNUP_INVITATION_TOKEN: int = 60 * 60 * 24
    YARA_AUTH_EXP_SIGNUP_VERIFICATION_TOKEN: int = 60 * 60 * 24
    YARA_AUTH_EXP_RESET_PASSWORD_VERIFICATION_TOKEN: int = 60 * 60 * 24

    # OAuth2
    YARA_OAUTH2_GOOGLE_CLIENT_ID: str = ""
    YARA_OAUTH2_GOOGLE_CLIENT_SECRET: str = ""

    # Websockets
    YARA_WEBSOCKETS_HANDLER_TASK: str | None = None
