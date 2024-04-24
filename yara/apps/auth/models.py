from uuid import UUID

from yara.apps.orm.models import UUIDModel


class Group(UUIDModel):
    __table__ = "yara__auth__group"

    name: str


class User(UUIDModel):
    __table__ = "yara__auth__user"

    group_id: UUID | None = None

    email: str
    phone: str | None
    full_name: str | None

    password: str

    is_active: bool = False
    is_superuser: bool = False
    is_group_moderator: bool = False
