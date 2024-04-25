import abc
import contextlib
import importlib
import logging
import typing as tp
from pkgutil import iter_modules

from yara.adapters.orm.backends.exceptions import UndefinedTableError
from yara.adapters.orm.backends.schemas import (
    ColumnClause,
    DeleteClause,
    EOperator,
    InsertClause,
    SelectClause,
    UniqueConstraintClause,
    UpdateClause,
    WhereClause,
    WhereTermClause,
)
from yara.settings import YaraSettings

logger = logging.getLogger(__name__)


class ORMBackend:
    settings: YaraSettings

    dsn: str
    migrations: list[str]
    migrations_table: str

    def __init__(
        self,
        settings: YaraSettings,
    ) -> None:
        self.settings = settings
        self.migrations_table = self.settings.YARA_ORM_MIGRATIONS_TABLE
        self.migrations = []
        for app_path in settings.get_apps_paths():
            migrations_path = f"{app_path}.migrations"
            try:
                importlib.import_module(migrations_path)
                self.migrations.append(migrations_path)
            except ImportError:
                continue

    @abc.abstractmethod
    async def up(self) -> None:
        ...

    @abc.abstractmethod
    async def healthcheck(self) -> bool:
        ...

    @abc.abstractmethod
    async def shutdown(self) -> None:
        ...

    @abc.abstractmethod
    def uow(self) -> tp.Any:
        ...

    @abc.abstractmethod
    async def execute(self, sql: str, *args: tp.Any, **kwargs: tp.Any) -> tp.Any:
        ...

    @abc.abstractmethod
    async def fetch(self, sql: str, *args: tp.Any, **kwargs: tp.Any) -> tp.Any:
        ...

    @abc.abstractmethod
    async def fetchval(self, sql: str, *args: tp.Any, **kwargs: tp.Any) -> tp.Any:
        ...

    @abc.abstractmethod
    async def create_table(
        self,
        table: str,
        columns: list[ColumnClause],
        unique_constraints: list[UniqueConstraintClause] | None = None,
    ) -> None:
        ...

    @abc.abstractmethod
    async def drop_table(
        self,
        table: str,
    ) -> None:
        ...

    @abc.abstractmethod
    async def alter_field(
        self,
        table: str,
        column: ColumnClause,
    ) -> None:
        ...

    @abc.abstractmethod
    async def select(
        self,
        table: str,
        clause: SelectClause,
    ) -> list[dict[str, tp.Any]]:
        ...

    @abc.abstractmethod
    async def delete(
        self,
        table: str,
        clause: DeleteClause,
    ) -> None:
        ...

    @abc.abstractmethod
    async def insert(
        self,
        table: str,
        clause: InsertClause,
    ) -> list[dict[str, tp.Any]]:
        ...

    @abc.abstractmethod
    async def update(
        self,
        table: str,
        clause: UpdateClause,
    ) -> list[dict[str, tp.Any]]:
        ...

    @abc.abstractmethod
    async def count(
        self,
        table: str,
        where: list[WhereClause] | None = None,
    ) -> int:
        ...

    @abc.abstractmethod
    async def exists(
        self,
        table: str,
        where: list[WhereClause] | None = None,
    ) -> bool:
        ...

    async def migrate(self, table: str) -> None:
        try:
            applied_migrations = [row["name"] for row in await self.select(table, SelectClause(columns=["name"]))]
        except UndefinedTableError:
            applied_migrations = []
        migration_modules = []
        for migrations_module_path in self.migrations:
            module = importlib.import_module(migrations_module_path)
            for migration_module_info in iter_modules(module.__path__):
                migration_module = importlib.import_module(migrations_module_path + "." + migration_module_info.name)
                if migration_module.__name__ in applied_migrations:
                    continue
                migration_modules.append(migration_module)
        async with self.uow():
            for migration_module in migration_modules:
                await migration_module.upgrade(self)
                await self.insert(
                    table,
                    InsertClause(
                        columns=["name"],
                        values=[migration_module.__name__],
                    ),
                )
                logger.info("%s applied", migration_module.__name__)

    async def makemigrations(self, table: str) -> bool:
        # TODO: implement me
        return False

    async def downgrade(self, table: str, to_migration: str | None = None) -> None:
        try:
            applied_migrations = [row["name"] for row in await self.select(table, SelectClause(columns=["name"]))]
        except UndefinedTableError:
            applied_migrations = []
        migration_modules = []
        for migrations_module_path in self.migrations:
            module = importlib.import_module(migrations_module_path)
            for migration_module_info in iter_modules(module.__path__):
                migration_module = importlib.import_module(migrations_module_path + "." + migration_module_info.name)
                if migration_module.__name__ not in applied_migrations:
                    continue
                migration_modules.append(migration_module)
        async with self.uow():
            for migration_module in migration_modules[::-1]:
                if to_migration and migration_module.__name__ == to_migration:
                    break
                await migration_module.downgrade(self)
                with contextlib.suppress(UndefinedTableError):
                    await self.delete(
                        table,
                        DeleteClause(
                            where=[
                                WhereClause(
                                    terms=[
                                        WhereTermClause(
                                            column="name",
                                            operator=EOperator.EQ,
                                            value=migration_module.__name__,
                                        ),
                                    ],
                                ),
                            ],
                        ),
                    )
                logger.info("%s deleted", migration_module.__name__)
