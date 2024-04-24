import logging
import typing as tp
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

import asyncpg
from asyncpg.transaction import Transaction

from yara.adapters.orm.backends.base import ORMBackend
from yara.adapters.orm.backends.exceptions import UndefinedTableError
from yara.adapters.orm.backends.schemas import (
    ColumnClause,
    DeleteClause,
    EColumnType,
    EOperator,
    InsertClause,
    SelectClause,
    UniqueConstraintClause,
    UpdateClause,
    WhereClause,
)

logger = logging.getLogger(__name__)


def _get_where_sql_with_values(where: list[WhereClause] | None, shift_index: int = 0) -> tuple[str, list[tp.Any]]:
    if not where:
        return "", []

    sql_where = " WHERE "
    values = []
    for index, where_clause in enumerate(where, start=1):
        sql_where += "("
        for subindex, where_clause_term in enumerate(where_clause.terms, start=1):
            values.append(where_clause_term.value)
            if where_clause_term.operator == EOperator.IN:
                sql_where += f"{where_clause_term.column} = tp.Any(${shift_index + len(values)})"
            else:
                sql_where += f"{where_clause_term.column} {where_clause_term.operator} ${shift_index + len(values)}"
            if subindex < len(where_clause.terms):
                sql_where += f" {where_clause.conjunction} "
        sql_where += ")"
        if index < len(where):
            sql_where += " AND "

    return sql_where, values


class ORMPostgresBackend(ORMBackend):
    connection_pool: asyncpg.Pool | None = None

    async def up(self) -> None:
        self.connection_pool: asyncpg.Pool = await asyncpg.create_pool(dsn=self.dsn)

    async def healthcheck(self) -> bool:
        assert self.connection_pool is not None
        connection: asyncpg.Connection
        async with self.connection_pool.acquire() as connection:
            return await connection.fetchval("SELECT 1") == 1

    async def shutdown(self) -> None:
        if self.connection_pool:
            await self.connection_pool.close()
            self.connection_pool = None

    @asynccontextmanager
    async def uow(self) -> AsyncGenerator[Transaction, None]:
        # Unit of work. Run all queries in a single transaction.
        assert self.connection_pool is not None
        connection: asyncpg.Connection
        async with (self.connection_pool.acquire() as connection, connection.transaction() as transaction):
            yield transaction

    async def execute(self, sql: str, *args: tp.Any, **kwargs: tp.Any) -> tp.Any:
        assert self.connection_pool is not None
        connection: asyncpg.Connection
        try:
            async with self.connection_pool.acquire() as connection:
                return await connection.execute(sql, *args, **kwargs)
        except asyncpg.exceptions.UndefinedTableError as e:
            raise UndefinedTableError(str(e)) from e

    async def fetch(self, sql: str, *args: tp.Any, **kwargs: tp.Any) -> tp.Any:
        assert self.connection_pool is not None
        connection: asyncpg.Connection
        try:
            async with self.connection_pool.acquire() as connection:
                return await connection.fetch(sql, *args, **kwargs)
        except asyncpg.exceptions.UndefinedTableError as e:
            raise UndefinedTableError(str(e)) from e

    async def fetchval(self, sql: str, *args: tp.Any, **kwargs: tp.Any) -> tp.Any:
        assert self.connection_pool is not None
        connection: asyncpg.Connection
        try:
            async with self.connection_pool.acquire() as connection:
                return await connection.fetchval(sql, *args, **kwargs)
        except asyncpg.exceptions.UndefinedTableError as e:
            raise UndefinedTableError(str(e)) from e

    async def create_table(
        self,
        table: str,
        columns: list[ColumnClause],
        unique_constraints: list[UniqueConstraintClause] | None = None,
    ) -> None:
        columns_with_types: list[str] = []
        sql_triggers: list[str] = []

        for column_clause in columns:
            sql_primary_key = " PRIMARY KEY" if column_clause.primary_key else ""
            sql_nullable = " NULL" if column_clause.nullable else " NOT NULL"
            match column_clause.type:
                case EColumnType.UUID:
                    sql_autogenerate = " DEFAULT gen_random_uuid()" if column_clause.primary_key else ""
                    sql_type = f"UUID{sql_nullable}{sql_autogenerate}{sql_primary_key}"
                case EColumnType.INT:
                    sql_int_type = "INTEGER"
                    sql_type = f"{sql_int_type}{sql_nullable}{sql_primary_key}"
                case EColumnType.SERIAL | EColumnType.BIGSERIAL | EColumnType.SMALLSERIAL | EColumnType.SMALLINT | EColumnType.BIGINT:
                    sql_number_type = column_clause.type.name
                    sql_type = f"{sql_number_type}{sql_nullable}{sql_primary_key}"
                case EColumnType.FLOAT:
                    sql_type = f"REAL{sql_nullable}"
                case EColumnType.BOOL:
                    sql_type = f"BOOLEAN{sql_nullable}"
                case EColumnType.STR:
                    sql_type = f"TEXT{sql_nullable}"
                case EColumnType.DATETIME:
                    sql_auto_now_add = " DEFAULT NOW()" if column_clause.auto_now_add or column_clause.auto_now else ""
                    sql_type = f"TIMESTAMP{sql_nullable}{sql_auto_now_add}"
                case EColumnType.DATETIME_TZ:
                    sql_auto_now_add = " DEFAULT NOW()" if column_clause.auto_now_add or column_clause.auto_now else ""
                    sql_type = f"TIMESTAMPTZ{sql_nullable}{sql_auto_now_add}"
                case EColumnType.DATE:
                    sql_auto_now_add = " DEFAULT NOW()" if column_clause.auto_now_add or column_clause.auto_now else ""
                    sql_type = f"DATE{sql_nullable}{sql_auto_now_add}"
                case EColumnType.DICT:
                    sql_type = f"JSONB{sql_nullable}"
                case EColumnType.LIST:
                    sql_type = f"TEXT[]{sql_nullable}"
                case _:
                    raise AssertionError(f"Unknown type {column_clause.type}")
            columns_with_types.append(f"{column_clause.name} {sql_type}")
            if column_clause.unique:
                columns_with_types.append(
                    f"CONSTRAINT {table}_{column_clause.name}_unique UNIQUE ({column_clause.name})"
                )
            if column_clause.fk_constraint:
                columns_with_types.append(
                    f"CONSTRAINT fk_{table}_{column_clause.name} FOREIGN KEY ({column_clause.name}) REFERENCES {column_clause.fk_constraint.table}({column_clause.fk_constraint.column}) ON DELETE {column_clause.fk_constraint.on_delete}"
                )
            if column_clause.auto_now and column_clause.type in ("DATETIME", "DATE"):
                sql_triggers.append(
                    f"""
                        CREATE OR REPLACE FUNCTION trigger_auto_now_{column_clause.name}()
                        RETURNS TRIGGER AS $$
                        BEGIN
                        NEW.{column_clause.name} = NOW();
                        RETURN NEW;
                        END;
                        $$ LANGUAGE plpgsql;
                    """
                )
                sql_triggers.append(
                    f"""
                        CREATE TRIGGER set_{table}_{column_clause.name}
                        BEFORE UPDATE ON {table}
                        FOR EACH ROW
                        EXECUTE PROCEDURE trigger_auto_now_{column_clause.name}();
                    """
                )

        sql_columns_with_types = ",".join(columns_with_types)
        sql = f"CREATE TABLE IF NOT EXISTS {table} ({sql_columns_with_types});"
        await self.execute(sql)
        if sql_triggers:
            for sql_trigger in sql_triggers:
                await self.execute(sql_trigger)

        if unique_constraints:
            for unique_constraint in unique_constraints:
                sql_column_names = "_".join(unique_constraint.columns)
                sql_columns = ",".join(unique_constraint.columns)
                sql = f"ALTER TABLE {table} ADD CONSTRAINT {table}_{sql_column_names}_unique UNIQUE ({sql_columns});"
                await self.execute(sql)

    async def drop_table(
        self,
        table: str,
    ) -> None:
        sql = f"DROP TABLE IF EXISTS {table};"
        await self.execute(sql)

    async def alter_field(
        self,
        table: str,
        column: ColumnClause,
    ) -> None:
        sql_triggers = []
        sql_primary_key = " PRIMARY KEY" if column.primary_key else ""
        sql_nullable = " NULL" if column.nullable else " NOT NULL"
        sql_auto_now_add = " DEFAULT NOW()" if column.auto_now_add or column.auto_now else ""
        sql = f"ALTER TABLE {table} ALTER COLUMN {column.name} TYPE {column.type}{sql_nullable}{sql_primary_key}{sql_auto_now_add};"
        await self.execute(sql)
        if column.auto_now and column.type in ("DATETIME", "DATE"):
            sql_triggers.append(
                f"""
                    CREATE OR REPLACE FUNCTION trigger_auto_now_{column.name}()
                    RETURNS TRIGGER AS $$
                    BEGIN
                    NEW.{column.name} = NOW();
                    RETURN NEW;
                    END;
                    $$ LANGUAGE plpgsql;
                """
            )
            sql_triggers.append(
                f"""
                    CREATE TRIGGER set_{table}_{column.name}
                    BEFORE UPDATE ON {table}
                    FOR EACH ROW
                    EXECUTE PROCEDURE trigger_auto_now_{column.name}();
                """
            )
        if sql_triggers:
            for sql_trigger in sql_triggers:
                await self.execute(sql_trigger)

    async def select(
        self,
        table: str,
        clause: SelectClause,
    ) -> list[dict[str, tp.Any]]:
        sql_where, values = _get_where_sql_with_values(clause.where)
        sql_distinct = "DISTINCT " if clause.distinct else ""
        sql_columns = ",".join(clause.columns) if clause.columns else "*"
        sql_order_by = ""
        if clause.order_by:
            sql_order_by = " ORDER BY "
            for index, order_by in enumerate(clause.order_by, start=1):
                sql_order_by += f"{order_by.column} {'DESC' if order_by.desc else 'ASC'}"
                if index < len(clause.order_by):
                    sql_order_by += ", "
        sql_pagination = (
            f" LIMIT {clause.pagination.limit} OFFSET {clause.pagination.offset}" if clause.pagination else ""
        )
        sql = f"SELECT {sql_distinct}{sql_columns} FROM {table}{sql_where}{sql_order_by}{sql_pagination};"  # noqa: S608
        records = await self.fetch(sql, *values)
        return [dict(record) for record in records or []]

    async def delete(
        self,
        table: str,
        clause: DeleteClause,
    ) -> None:
        sql_where, values = _get_where_sql_with_values(clause.where)
        sql = f"DELETE FROM {table}{sql_where};"  # noqa: S608
        await self.execute(sql, *values)

    async def insert(
        self,
        table: str,
        clause: InsertClause,
    ) -> list[dict[str, tp.Any]]:
        sql_columns = ",".join(clause.columns)
        sql_values = ",".join([f"${index}" for index, _ in enumerate(clause.values, start=1)])
        sql_returning = f" RETURNING {','.join(clause.returning)}" if clause.returning else ""
        sql = f"INSERT INTO {table} ({sql_columns}) VALUES ({sql_values}){sql_returning};"  # noqa: S608
        records = await self.fetch(sql, *clause.values)
        return [dict(record) for record in records or []]

    async def update(
        self,
        table: str,
        clause: UpdateClause,
    ) -> list[dict[str, tp.Any]]:
        if not clause.columns:
            return []
        sql_columns = ",".join([f"{i} = ${index}" for index, i in enumerate(clause.columns, start=1)])
        sql_returning = f" RETURNING {','.join(clause.returning)}" if clause.returning else ""
        sql_where, where_values = _get_where_sql_with_values(clause.where, shift_index=len(clause.values))
        sql = f"UPDATE {table} SET {sql_columns}{sql_where}{sql_returning};"  # noqa: S608
        records = await self.fetch(sql, *clause.values, *where_values)
        return [dict(record) for record in records or []]

    async def count(
        self,
        table: str,
        where: list[WhereClause] | None = None,
    ) -> int:
        sql_where, values = _get_where_sql_with_values(where)
        sql = f"SELECT COUNT(*) FROM {table}{sql_where};"  # noqa: S608
        return await self.fetchval(sql, *values)

    async def exists(
        self,
        table: str,
        where: list[WhereClause] | None = None,
    ) -> bool:
        sql_where, values = _get_where_sql_with_values(where)
        sql = f"SELECT EXISTS(SELECT 1 FROM {table}{sql_where});"  # noqa: S608
        return await self.fetchval(sql, *values)
