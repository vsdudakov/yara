import enum
import typing as tp
from datetime import date, datetime

from pydantic import BaseModel, field_validator


class EColumnType(enum.StrEnum):
    BOOL = "BOOL"
    STR = "STR"
    INT = "INT"
    SMALLINT = "SMALLINT"
    BIGINT = "BIGINT"
    FLOAT = "FLOAT"
    DATETIME = "DATETIME"
    DATETIME_TZ = "DATETIME_TZ"
    DATE = "DATE"
    LIST = "LIST"
    DICT = "DICT"
    UUID = "UUID"
    SERIAL = "SERIAL"
    SMALLSERIAL = "SMALLSERIAL"
    BIGSERIAL = "BIGSERIAL"


class EOperator(enum.StrEnum):
    EQ = "="
    NOT_EQ = "!="
    GT = ">"
    LT = "<"
    GTE = ">="
    LTE = "<="
    LIKE = "LIKE"
    IN = "IN"
    IS = "IS"
    IS_NOT = "IS NOT"


class EAction(enum.StrEnum):
    CASCADE = "CASCADE"
    SET_NULL = "SET NULL"
    RESTRICT = "RESTRICT"
    NO_ACTION = "NO ACTION"


class UniqueConstraintClause(BaseModel):
    columns: list[str]


class FkConstraintClause(BaseModel):
    table: str
    column: str
    on_delete: EAction


class ColumnClause(BaseModel):
    name: str
    type: EColumnType
    primary_key: bool = False
    auto_now_add: bool = False
    auto_now: bool = False
    nullable: bool = False
    unique: bool = False
    fk_constraint: FkConstraintClause | None = None
    # TODO: implement default logic
    default: tp.Any | None = None


class WhereTermClause(BaseModel):
    column: str
    operator: EOperator
    value: tp.Any

    @field_validator("value", mode="after")
    @classmethod
    def validate_value(cls, value: tp.Any) -> tp.Any:
        if not isinstance(
            value,
            bool | str | int | float | datetime | date | list | dict | None,
        ):
            raise ValueError("Invalid value")
        if isinstance(value, list) and (
            not all(isinstance(x, bool) for x in value)
            and not all(isinstance(x, str) for x in value)
            and not all(isinstance(x, int) for x in value)
            and not all(isinstance(x, float) for x in value)
            and not all(isinstance(x, datetime) for x in value)
        ):
            raise ValueError("Invalid value")
        return value


class WhereClause(BaseModel):
    terms: list[WhereTermClause]
    conjunction: tp.Literal["AND", "OR"] | None = "AND"


class OrderClause(BaseModel):
    column: str
    desc: bool = False


class PaginationClause(BaseModel):
    offset: int = 0
    limit: int = 50


class SelectClause(BaseModel):
    columns: list[str] | None = None
    where: list[WhereClause] | None = None
    order_by: list[OrderClause] | None = None
    pagination: PaginationClause | None = None
    distinct: bool = False


class DeleteClause(BaseModel):
    where: list[WhereClause] | None = None


class InsertClause(BaseModel):
    columns: list[str]
    values: list[tp.Any]
    returning: list[str] | None = None


class UpdateClause(BaseModel):
    columns: list[str]
    values: list[tp.Any]
    where: list[WhereClause] | None = None
    returning: list[str] | None = None


def where_clause(**kwargs: tp.Any) -> list[WhereClause]:
    terms = []
    for k, v in kwargs.items():
        operator = EOperator.EQ
        if k.endswith("__not"):
            operator = EOperator.NOT_EQ
            k = k.replace("__not", "")
        elif k.endswith("__in"):
            operator = EOperator.IN
            k = k.replace("__in", "")
        elif k.endswith("__gt"):
            operator = EOperator.GT
            k = k.replace("__gt", "")
        elif k.endswith("__lt"):
            operator = EOperator.LT
            k = k.replace("__lt", "")
        elif k.endswith("__gte"):
            operator = EOperator.GTE
            k = k.replace("__gte", "")
        elif k.endswith("__lte"):
            operator = EOperator.LTE
            k = k.replace("__lte", "")
        elif k.endswith("__like"):
            operator = EOperator.LIKE
            k = k.replace("__like", "")
        elif k.endswith("__is"):
            operator = EOperator.IS
            k = k.replace("__is", "")
        elif k.endswith("__is_not"):
            operator = EOperator.IS_NOT
            k = k.replace("__is_not", "")
        terms.append(
            WhereTermClause(
                column=k,
                operator=operator,
                value=v,
            )
        )
    return [WhereClause(terms=terms)]
