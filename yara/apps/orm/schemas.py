import typing as tp

from pydantic import BaseModel

from yara.apps.orm.models import UUIDModel

TModel = tp.TypeVar("TModel", bound=UUIDModel)


class ListResponse(BaseModel, tp.Generic[TModel]):
    results: list[TModel]
    total: int
