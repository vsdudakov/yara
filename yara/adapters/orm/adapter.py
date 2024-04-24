import typing as tp

from yara.adapters.orm.backends.base import ORMBackend
from yara.adapters.orm.backends.schemas import (
    DeleteClause,
    InsertClause,
    PaginationClause,
    SelectClause,
    UpdateClause,
    WhereClause,
    where_clause,
)
from yara.apps.orm.models import Model
from yara.core.adapters import YaraAdapter
from yara.core.helpers import import_obj
from yara.main import YaraBaseRootApp

TModel = tp.TypeVar("TModel", bound=Model)


class ORMAdapter(tp.Generic[TModel], YaraAdapter):
    backend: ORMBackend
    root_app: YaraBaseRootApp

    def __init__(self, root_app: YaraBaseRootApp) -> None:
        super().__init__(root_app)
        backend_cls_path: str | None = getattr(self.root_app.settings, "YARA_ORM_BACKEND", None)
        if not backend_cls_path:
            raise ValueError("Provide YARA_ORM_BACKEND setting")

        backend_cls: type[ORMBackend] | None = import_obj(backend_cls_path)
        if not backend_cls:
            raise ValueError(f"Backend {backend_cls_path} not found")

        self.backend = backend_cls(self.root_app.settings)

    async def up(self) -> None:
        await self.backend.up()

    async def healthcheck(self) -> bool:
        return await self.backend.healthcheck()

    async def shutdown(self) -> None:
        await self.backend.shutdown()

    async def list_rows(
        self,
        model_cls: type[TModel],
        clause: SelectClause,
    ) -> tuple[list[TModel] | list[dict[str, tp.Any]], int]:
        rows = await self.backend.select(
            model_cls.__table__,
            clause,
        )
        clause.pagination = None
        total = await self.backend.count(
            model_cls.__table__,
            clause.where,
        )
        if clause.columns is not None:
            return rows, total
        return [model_cls.serialize(row) for row in rows], total

    async def read(
        self,
        model_cls: type[TModel],
        where: list[WhereClause],
    ) -> TModel | None:
        rows = await self.backend.select(
            model_cls.__table__,
            SelectClause(
                where=where,
                pagination=PaginationClause(
                    limit=2,  # check if there are multiple rows
                ),
            ),
        )
        if len(rows) > 1:
            raise Exception("Multiple rows returned")
        if len(rows) == 0:
            return None
        return model_cls.serialize(rows[0])

    async def create(
        self,
        model_cls: type[TModel],
        payload: dict[str, tp.Any],
        returning: list[str] | None = None,
    ) -> dict[str, tp.Any]:
        rows = await self.backend.insert(
            model_cls.__table__,
            InsertClause(
                columns=list(payload.keys()),
                values=list(payload.values()),
                returning=returning,
            ),
        )
        if rows:
            return rows[0]
        return {}

    async def update(
        self,
        model_cls: type[TModel],
        payload: dict[str, tp.Any],
        where: list[WhereClause],
        returning: list[str] | None = None,
    ) -> dict[str, tp.Any]:
        results = await self.backend.update(
            model_cls.__table__,
            UpdateClause(
                columns=list(payload.keys()),
                values=list(payload.values()),
                where=where,
                returning=returning,
            ),
        )
        if results:
            return results[0]
        return {}

    async def delete(
        self,
        model_cls: type[TModel],
        where: list[WhereClause],
    ) -> None:
        await self.backend.delete(
            model_cls.__table__,
            DeleteClause(
                where=where,
            ),
        )

    async def create_and_read(
        self,
        model_cls: type[TModel],
        payload: dict[str, tp.Any],
    ) -> TModel:
        async with self.backend.uow():
            row = await self.create(
                model_cls,
                payload,
                returning=["id"],
            )
            assert row
            obj = await self.read(
                model_cls,
                where_clause(id=str(row["id"])),
            )
            assert obj
            return obj

    async def update_and_read(
        self,
        model_cls: type[TModel],
        payload: dict[str, tp.Any],
        where: list[WhereClause],
    ) -> TModel | None:
        async with self.backend.uow():
            row = await self.update(
                model_cls,
                payload,
                where,
                returning=["id"],
            )
            if not row:
                return None
            return await self.read(
                model_cls,
                where_clause(id=str(row["id"])),
            )

    async def update_or_create(
        self,
        model_cls: type[TModel],
        payload: dict[str, tp.Any],
        where: list[WhereClause],
    ) -> TModel:
        # TODO: select for update
        async with self.backend.uow():
            row = await self.update_and_read(
                model_cls,
                payload,
                where,
            )
            if row:
                return row
            return await self.create_and_read(
                model_cls,
                payload,
            )

    async def read_or_create(
        self,
        model_cls: type[TModel],
        payload: dict[str, tp.Any],
        where: list[WhereClause],
    ) -> TModel:
        async with self.backend.uow():
            row = await self.read(
                model_cls,
                where,
            )
            if row:
                return row
            return await self.create_and_read(
                model_cls,
                payload,
            )

    async def exists(
        self,
        model_cls: type[TModel],
        where: list[WhereClause],
    ) -> bool:
        return await self.backend.exists(
            model_cls.__table__,
            where=where,
        )

    async def count(
        self,
        model_cls: type[TModel],
        where: list[WhereClause],
    ) -> int:
        return await self.backend.count(
            model_cls.__table__,
            where=where,
        )
