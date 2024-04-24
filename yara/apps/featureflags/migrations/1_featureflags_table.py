from yara.adapters.orm.adapter import ORMBackend
from yara.adapters.orm.backends.schemas import ColumnClause, EColumnType, UniqueConstraintClause


async def upgrade(orm_backend: ORMBackend) -> None:
    await orm_backend.create_table(
        "yara__featureflags__featureflag",
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
                name="for_id",
                type=EColumnType.UUID,
            ),
            ColumnClause(
                name="for_type",
                type=EColumnType.STR,
            ),
            ColumnClause(
                name="feature_flag",
                type=EColumnType.STR,
                unique=True,
            ),
            ColumnClause(
                name="enabled",
                type=EColumnType.BOOL,
            ),
        ],
        unique_constraints=[
            UniqueConstraintClause(
                columns=["for_id", "for_type", "feature_flag"],
            ),
        ],
    )


async def downgrade(orm_backend: ORMBackend) -> None:
    await orm_backend.drop_table("yara__featureflags__featureflag")
