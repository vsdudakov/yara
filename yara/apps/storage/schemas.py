from pydantic import BaseModel

from yara.apps.storage.models import File


class CreateFilePayload(BaseModel):
    name: str | None
    content_type: str | None

    bucket_name: str
    path: str


class UpdateFilePayload(BaseModel):
    name: str | None = None
    is_uploaded: bool | None = False


class FileWithPresignedUploadUrlResponse(File):
    presigned_upload_url: str | None


class FileWithPresignedDownloadUrlResponse(File):
    presigned_download_url: str | None
