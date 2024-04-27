from pydantic import BaseModel

from yara.apps.storage.models import File


class CreateFile(BaseModel):
    name: str | None
    content_type: str | None

    bucket_name: str
    path: str


class FileWithPresignedUploadUrl(File):
    presigned_upload_url: str | None


class FileWithPresignedDownloadUrl(File):
    presigned_download_url: str | None
