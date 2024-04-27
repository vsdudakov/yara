from yara.apps.orm.models import UUIDModel


class File(UUIDModel):
    __table__ = "yara__storage__file"

    name: str | None
    content_type: str | None

    bucket_name: str
    path: str
    is_uploaded: bool = False
