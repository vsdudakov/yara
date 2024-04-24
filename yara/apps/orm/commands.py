import typing as tp

from yara.adapters.orm.adapter import ORMAdapter
from yara.core.commands import Option, command, echo


@command
async def migrate(root_app=Option(None, hidden=True)) -> None:  # type: ignore [no-untyped-def]
    orm_adapter: ORMAdapter[tp.Any] = root_app.get_adapter(ORMAdapter)
    await orm_adapter.backend.migrate("yara__orm__migrations")
    echo("Database has been migrated")


@command
async def downgrade(root_app=Option(None, hidden=True)) -> None:  # type: ignore [no-untyped-def]
    orm_adapter: ORMAdapter[tp.Any] = root_app.get_adapter(ORMAdapter)
    await orm_adapter.backend.downgrade("yara__orm__migrations")
    echo("Database has been downgraded")
