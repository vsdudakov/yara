from yara.adapters.orm.adapter import ORMBackend
from yara.adapters.orm.backends.schemas import ColumnClause, EAction, EColumnType, FkConstraintClause


async def upgrade(orm_backend: ORMBackend) -> None:
    await orm_backend.create_table(
        "yara__auth__user",
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
                name="group_id",
                type=EColumnType.UUID,
                nullable=True,
                fk_constraint=FkConstraintClause(
                    table="yara__auth__group",
                    column="id",
                    on_delete=EAction.SET_NULL,
                ),
            ),
            ColumnClause(
                name="email",
                type=EColumnType.STR,
                unique=True,
            ),
            ColumnClause(
                name="phone",
                type=EColumnType.STR,
                nullable=True,
                unique=True,
            ),
            ColumnClause(
                name="full_name",
                type=EColumnType.STR,
                nullable=True,
            ),
            ColumnClause(
                name="password",
                type=EColumnType.STR,
            ),
            ColumnClause(
                name="is_active",
                type=EColumnType.BOOL,
                default=False,
            ),
            ColumnClause(
                name="is_superuser",
                type=EColumnType.BOOL,
                default=False,
            ),
            ColumnClause(
                name="is_group_moderator",
                type=EColumnType.BOOL,
                default=False,
            ),
        ],
    )


async def downgrade(orm_backend: ORMBackend) -> None:
    await orm_backend.drop_table("yara__auth__user")
