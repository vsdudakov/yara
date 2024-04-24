from yara.adapters.storage.backends.base import StorageBackend
from yara.core.adapters import YaraAdapter
from yara.core.helpers import import_class
from yara.main import YaraBaseRootApp


class StorageAdapter(YaraAdapter):
    backend: StorageBackend
    root_app: YaraBaseRootApp

    def __init__(self, root_app: YaraBaseRootApp) -> None:
        super().__init__(root_app)
        backend_cls_path: str | None = getattr(self.root_app.settings, "YARA_STORAGE_BACKEND", None)

        if not backend_cls_path:
            raise ValueError("Provide YARA_STORAGE_BACKEND settings")

        backend_cls: type[StorageBackend] | None = import_class(backend_cls_path)
        if not backend_cls:
            raise ValueError(f"Backend {backend_cls_path} not found")

        self.backend = backend_cls(self.root_app.settings)

    async def up(self) -> None:
        await self.backend.up()

    async def healthcheck(self) -> bool:
        return await self.backend.healthcheck()

    async def shutdown(self) -> None:
        await self.backend.shutdown()

    async def presigned_get_object(self, bucket_name: str, object_name: str) -> str | None:
        return await self.backend.presigned_get_object(bucket_name, object_name)

    async def presigned_put_object(self, bucket_name: str, object_name: str) -> str | None:
        return await self.backend.presigned_put_object(bucket_name, object_name)

    async def remove_object(self, bucket_name: str, object_name: str) -> None:
        await self.backend.remove_object(bucket_name, object_name)

    async def remove_objects(self, bucket_name: str, object_names: list[str]) -> None:
        await self.backend.remove_objects(bucket_name, object_names)
