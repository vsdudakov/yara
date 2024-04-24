import asyncio
import importlib
import logging
import logging.config
import os
import typing as tp
from abc import abstractmethod
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

import sentry_sdk
from celery import Celery
from dotenv import load_dotenv
from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse
from sentry_sdk.integrations.fastapi import FastApiIntegration
from sentry_sdk.integrations.logging import LoggingIntegration
from sentry_sdk.integrations.starlette import StarletteIntegration

from yara.core.adapters import YaraAdapter
from yara.core.apps import YaraApp
from yara.core.helpers import import_class
from yara.core.tasks import AsyncCeleryTask
from yara.settings import YaraSettings

logger = logging.getLogger(__name__)
load_dotenv(os.getenv("YARA_ENV_FILE") or ".env")


@asynccontextmanager
async def fastapi_app_lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    yara_root_app: "YaraRootApp" = app.extra["yara_root_app"]
    await yara_root_app.up_adapters()
    if not await yara_root_app.healthcheck_adapters():
        raise Exception("Yara adapters are not healthy")
    yield
    await yara_root_app.shutdown_adapters()


async def value_error_exp_handler(_: Request, exc: ValueError) -> JSONResponse:
    """
    Exception handler for ValueError.
    Formats the error message to be returned to the client.
    """
    try:
        field_errors = exc.args[0]
    except IndexError:
        field_errors = {}
    if not isinstance(field_errors, dict):
        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            content={"detail": [{"loc": ["body"], "msg": field_errors, "type": ""}]},
        )

    errors = []
    for field, error in field_errors.items():
        errors.append({"loc": ["body", field], "msg": error, "type": ""})

    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={"detail": errors},
    )


class YaraBaseRootApp:
    settings: YaraSettings
    adapters: dict[type[YaraAdapter], YaraAdapter]

    def __init__(self) -> None:
        settings_path = os.getenv("YARA_SETTINGS")
        if not settings_path:
            raise ValueError("YARA_SETTINGS environment variable is not set")
        settings_cls: type[YaraSettings] | None = import_class(settings_path)
        if not settings_cls:
            raise ValueError(f"Settings {settings_path} not found")
        self.settings = settings_cls()  # type: ignore [call-arg]

        self.adapters = {}
        for adapter_cls_path in self.settings.YARA_ADAPTERS:
            adapter_cls: type[YaraAdapter] | None = import_class(adapter_cls_path)
            if not adapter_cls:
                logger.error("Adapter %s not found", adapter_cls_path)
                continue
            self.adapters[adapter_cls] = adapter_cls(self)

        self.init_sentry()
        self.config_logging()

    @abstractmethod
    def get_asgi_app(self) -> tp.Any:
        """
        Get the ASGI app.
        """
        ...

    async def up_adapters(self) -> None:
        await asyncio.gather(*(a.up() for a in self.adapters.values()))

    async def healthcheck_adapters(self) -> bool:
        return all(await asyncio.gather(*(a.healthcheck() for a in self.adapters.values())))

    async def shutdown_adapters(self) -> None:
        await asyncio.gather(*(a.shutdown() for a in self.adapters.values()))

    def get_adapter(self, adapter_cls: type[YaraAdapter]) -> tp.Any:
        adapter = self.adapters.get(adapter_cls)
        if not adapter:
            raise ValueError(f"Adapter {adapter_cls} not found")
        return adapter

    def init_sentry(self) -> None:
        if not self.settings.YARA_SENTRY_DSN:
            return
        sentry_sdk.init(
            dsn=self.settings.YARA_SENTRY_DSN,
            integrations=[
                StarletteIntegration(transaction_style="endpoint"),
                FastApiIntegration(transaction_style="endpoint"),
                LoggingIntegration(
                    level=logging.INFO,  # Capture info and above as breadcrumbs
                    event_level=logging.ERROR,  # Send errors as events
                ),
            ],
            traces_sample_rate=self.settings.YARA_SENTRY_TRACES_SAMPLE_RATE,
            environment=self.settings.YARA_ENV,
        )

    def config_logging(self) -> None:
        logging.config.dictConfig(
            {
                "version": 1,
                "disable_existing_loggers": False,
                "formatters": {
                    "console": {
                        "class": "logging.Formatter",
                        "datefmt": "%H:%M:%S",
                        "format": "%(levelname)s:\t\b%(asctime)s %(name)s:%(lineno)d %(message)s",
                    },
                },
                "handlers": {
                    "console": {
                        "class": "logging.StreamHandler",
                        "formatter": "console",
                    },
                },
                "loggers": {
                    "root": {
                        "handlers": ["console"],
                        "level": self.settings.YARA_LOGGING_LEVEL,
                        "propagate": True,
                    },
                },
            }
        )


class YaraRootApp(YaraBaseRootApp):
    fastapi_app: FastAPI
    apps: dict[type[YaraApp], YaraApp]

    def __init__(self) -> None:
        super().__init__()
        self.fastapi_app = FastAPI(
            title=self.settings.YARA_PROJECT_NAME,
            lifespan=fastapi_app_lifespan,
            yara_root_app=self,
        )
        self.fastapi_app.add_exception_handler(ValueError, value_error_exp_handler)

        self.apps = {}
        for app_cls_path in self.settings.YARA_APPS:
            app_cls: type[YaraApp] | None = import_class(app_cls_path)
            if not app_cls:
                logger.error("App %s not found", app_cls_path)
                continue
            self.apps[app_cls] = app_cls(self)

        for app in self.apps.values():
            if app.middlewares:
                for middleware_cls, options in app.middlewares:
                    self.fastapi_app.add_middleware(middleware_cls, **options)

        for app in self.apps.values():
            if app.api_router:
                self.fastapi_app.include_router(app.api_router)

    def get_asgi_app(self) -> tp.Any:
        return self.fastapi_app


class YaraCeleryApp(YaraBaseRootApp):
    celery_app: Celery

    def __init__(self) -> None:
        super().__init__()
        include_tasks = []
        for app_path in self.settings.get_apps_paths():
            tasks_path = f"{app_path}.tasks"
            try:
                importlib.import_module(tasks_path)
                include_tasks.append(tasks_path)
            except ImportError:
                continue

        self.celery_app = Celery(
            broker=self.settings.YARA_CELERY_BROKER_URI,
            backend=self.settings.YARA_CELERY_RESULT_BACKEND_URI,
            include=include_tasks,
            task_cls=AsyncCeleryTask,
        )

    def get_asgi_app(self) -> tp.Any:
        return self.celery_app


root_app = YaraRootApp()
root_asgi_app = root_app.get_asgi_app()

celery_app = YaraCeleryApp()
celery_asgi_app = celery_app.get_asgi_app()
