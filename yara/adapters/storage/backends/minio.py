import logging

from aiohttp import ClientConnectorError
from miniopy_async import Minio, deleteobjects

from yara.adapters.storage.backends.base import StorageBackend
from yara.settings import YaraSettings

logger = logging.getLogger(__name__)


class MinioStorageBackend(StorageBackend):
    settings: YaraSettings

    client: Minio | None

    async def up(self) -> None:
        self.client = Minio(
            self.settings.YARA_STORAGE_MINIO_URL,
            access_key=self.settings.YARA_STORAGE_MINIO_ACCESS_KEY,
            secret_key=self.settings.YARA_STORAGE_MINIO_SECRET_KEY,
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
