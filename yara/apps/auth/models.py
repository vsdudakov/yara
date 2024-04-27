import uuid

from yara.apps.orm.models import UUIDModel


class User(UUIDModel):
    __table__ = "yara__auth__user"

    email: str
    full_name: str | None
    avatar_id: uuid.UUID | None

    password: str

    is_active: bool = False
    is_superuser: bool = False
