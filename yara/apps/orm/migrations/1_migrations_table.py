from yara.adapters.orm.adapter import ORMBackend
from yara.adapters.orm.backends.schemas import ColumnClause, EColumnType


async def upgrade(orm_backend: ORMBackend) -> None:
    await orm_backend.create_table(
        orm_backend.migrations_table,
        columns=[
            ColumnClause(
                name="id",
                type=EColumnType.UUID,
                primary_key=True,
            ),
            ColumnClause(
                name="name",
                type=EColumnType.STR,
            ),
            ColumnClause(
                name="created_at",
                type=EColumnType.DATETIME_TZ,
                auto_now_add=True,
            ),
            ColumnClause(
                name="updated_at",
                type=EColumnType.DATETIME_TZ,
                auto_now=True,
            ),
        ],
    )


async def downgrade(orm_backend: ORMBackend) -> None:
    await orm_backend.drop_table(orm_backend.migrations_table)
