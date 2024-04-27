from uuid import UUID

from yara.apps.storage import schemas
from yara.apps.storage.services import StorageService
from yara.core.api_routers import Depends, HTTPException, YaraApiRouter, get_service, status

api_router = YaraApiRouter(
    prefix="/storage",
    tags=["storage"],
)


@api_router.post("")
async def create_file(
    payload: schemas.CreateFilePayload,
    storage_service: StorageService = Depends(get_service(StorageService)),
) -> schemas.FileWithPresignedUploadUrlResponse:
    return await storage_service.create_file(payload)


@api_router.patch("/{id}")
async def update_file(
    id: UUID,
    payload: schemas.UpdateFilePayload,
    storage_service: StorageService = Depends(get_service(StorageService)),
) -> None:
    await storage_service.update_file(id, payload)


@api_router.get("/{id}")
async def retrieve_file(
    id: UUID,
    storage_service: StorageService = Depends(get_service(StorageService)),
) -> schemas.FileWithPresignedDownloadUrlResponse:
    file_with_presigned_download_url = await storage_service.retrieve_file(id)
    if not file_with_presigned_download_url:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="File not found")
    return file_with_presigned_download_url


@api_router.delete("/{id}")
async def delete_file(
    id: UUID,
    storage_service: StorageService = Depends(get_service(StorageService)),
) -> None:
    await storage_service.delete_file(id)
