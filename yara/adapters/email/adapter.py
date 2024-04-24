import typing as tp

from yara.adapters.email.backends.base import EmailBackend
from yara.core.adapters import YaraAdapter
from yara.core.helpers import import_class
from yara.main import YaraBaseRootApp


class EmailAdapter(YaraAdapter):
    backend: EmailBackend
    root_app: YaraBaseRootApp

    def __init__(self, root_app: YaraBaseRootApp) -> None:
        super().__init__(root_app)
        backend_cls_path: str | None = getattr(self.root_app.settings, "YARA_EMAIL_BACKEND", None)

        if not backend_cls_path:
            raise ValueError("Provide YARA_EMAIL_BACKEND settings")

        backend_cls: type[EmailBackend] | None = import_class(backend_cls_path)
        if not backend_cls:
            raise ValueError(f"Backend {backend_cls_path} not found")

        self.backend = backend_cls(self.root_app.settings)

    async def up(self) -> None:
        await self.backend.up()

    async def healthcheck(self) -> bool:
        return await self.backend.healthcheck()

    async def shutdown(self) -> None:
        await self.backend.shutdown()

    async def send_email(self, to: str, template_id: str, payload: dict[str, tp.Any]) -> None:
        await self.backend.send_email(to, template_id, payload)
