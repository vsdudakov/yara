from yara.adapters.orm.adapter import ORMBackend
from yara.adapters.orm.backends.schemas import ColumnClause, EColumnType


async def upgrade(orm_backend: ORMBackend) -> None:
    await orm_backend.create_table(
        "yara__storage__file",
        [
            ColumnClause(
                name="id",
                type=EColumnType.UUID,
                primary_key=True,
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
            ColumnClause(
                name="name",
                type=EColumnType.STR,
                nullable=True,
            ),
            ColumnClause(
                name="content_type",
                type=EColumnType.STR,
                nullable=True,
            ),
            ColumnClause(
                name="bucket_name",
                type=EColumnType.STR,
            ),
            ColumnClause(
                name="path",
                type=EColumnType.STR,
            ),
            ColumnClause(
                name="is_uploaded",
                type=EColumnType.BOOL,
                default=False,
            ),
        ],
    )


async def downgrade(orm_backend: ORMBackend) -> None:
    await orm_backend.drop_table("yara__storage__file")
