import logging
import uuid

from yara.adapters.orm.adapter import ORMAdapter, where_clause
from yara.adapters.storage.adapter import StorageAdapter
from yara.apps.storage import schemas
from yara.apps.storage.models import File
from yara.core.services import YaraService
from yara.main import YaraRootApp

logger = logging.getLogger(__name__)


class StorageService(YaraService):
    file_orm_adapter: ORMAdapter[File]
    storage_adapter: StorageAdapter
    bucket_name: str

    def __init__(self, root_app: YaraRootApp, bucket_name: str = "storage") -> None:
        super().__init__(root_app)
        self.file_orm_adapter: ORMAdapter[File] = self.root_app.get_adapter(ORMAdapter)
        self.storage_adapter: StorageAdapter = self.root_app.get_adapter(StorageAdapter)
        self.bucket_name = bucket_name

    async def get_presigned_upload_url(self, path: str) -> str | None:
        return await self.storage_adapter.presigned_put_object(self.bucket_name, path)

    async def get_presigned_download_url(self, id: uuid.UUID) -> str | None:
        file = await self.file_orm_adapter.read(File, where_clause(id=id))
        if file is None:
            logger.warning("File with id %s not found", id)
            return None
        return await self.storage_adapter.presigned_get_object(self.bucket_name, file.path)

    async def create_file(self, payload: schemas.CreateFile) -> schemas.FileWithPresignedUploadUrl:
        file = await self.file_orm_adapter.create_and_read(File, payload.model_dump())
        presigned_upload_url = await self.get_presigned_upload_url(file.path)
        return schemas.FileWithPresignedUploadUrl(**file.model_dump(), presigned_upload_url=presigned_upload_url)

    async def retrieve_file(self, id: uuid.UUID) -> schemas.FileWithPresignedDownloadUrl | None:
        file = await self.file_orm_adapter.read(File, where_clause(id=id))
        if file is None:
            return None
        presigned_download_url = await self.get_presigned_download_url(id)
        return schemas.FileWithPresignedDownloadUrl(**file.model_dump(), presigned_download_url=presigned_download_url)

    async def delete_file(self, id: uuid.UUID) -> None:
        file = await self.file_orm_adapter.read(File, where_clause(id=id))
        if file is None:
            logger.warning("File with id %s not found", id)
            return
        with self.file_orm_adapter.backend.uow():
            await self.file_orm_adapter.delete(File, where_clause(id=id))
            await self.storage_adapter.remove_object(self.bucket_name, file.path)
