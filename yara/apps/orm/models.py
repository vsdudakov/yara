import typing as tp
from datetime import datetime
from uuid import UUID

from pydantic import BaseModel


class Model(BaseModel):
    __table__: str

    @classmethod
    def serialize(cls: type["Model"], row: dict[str, tp.Any]) -> tp.Any:
        return cls.model_validate(row)

    def deserialize(self) -> dict[str, tp.Any]:
        return self.model_dump()


class UUIDModel(Model):
    id: UUID
    created_at: datetime
    updated_at: datetime


class Migration(UUIDModel):
    __table__ = "yara__orm__migrations"

    name: str
