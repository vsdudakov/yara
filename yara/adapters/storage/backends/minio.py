import logging
import typing as tp

from aiohttp import ClientConnectorError
from miniopy_async import Minio, deleteobjects

from yara.adapters.storage.backends.base import StorageBackend
from yara.settings import YaraSettings

logger = logging.getLogger(__name__)


class MinioStorageBackend(StorageBackend):
    settings: YaraSettings

    client: Minio | None
    minio_url: str
    minio_access_key: str
    minio_secret_key: str

    def __init__(
        self,
        settings: YaraSettings,
    ) -> None:
        super().__init__(settings)
        for setting, field, required in (
            ("YARA_STORAGE_MINIO_URL", "minio_url", True),
            ("YARA_STORAGE_MINIO_ACCESS_KEY", "minio_access_key", True),
            ("YARA_STORAGE_MINIO_SECRET_KEY", "minio_secret_key", True),
        ):
            value: tp.Any | None = getattr(settings, setting, None)
            if value is None and required:
                raise ValueError(f"Provide {setting} settings")
            setattr(self, field, value)

    async def up(self) -> None:
        self.client = Minio(
            self.minio_url,
            access_key=self.minio_access_key,
            secret_key=self.minio_secret_key,
            secure=False,
        )

    async def healthcheck(self) -> bool:
        return self.client is not None

    async def shutdown(self) -> None:
        self.client = None

    async def presigned_get_object(self, bucket_name: str, object_name: str) -> str | None:
        if not self.client:
            return None
        try:
            return await self.client.presigned_get_object(bucket_name, object_name)
        except ClientConnectorError:
            logger.exception("Minio connection error")
            return None

    async def presigned_put_object(self, bucket_name: str, object_name: str) -> str | None:
        if not self.client:
            return None
        try:
            return await self.client.presigned_put_object(bucket_name, object_name)
        except ClientConnectorError:
            logger.exception("Minio connection error")
            return None

    async def remove_object(self, bucket_name: str, object_name: str) -> None:
        if not self.client:
            return
        try:
            await self.client.remove_object(bucket_name, object_name)
        except ClientConnectorError:
            logger.exception("Minio connection error")
            return

    async def remove_objects(self, bucket_name: str, object_names: list[str]) -> None:
        if not self.client:
            return
        delete_object_list = [deleteobjects.DeleteObject(object_name) for object_name in object_names]
        try:
            await self.client.remove_objects(bucket_name, delete_object_list)
        except ClientConnectorError:
            logger.exception("Minio connection error")
            return
