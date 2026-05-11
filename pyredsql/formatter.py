from __future__ import annotations

from abc import ABC, abstractmethod

import sqlglot

from pyredsql.errors import FormatterError


class FormatterBackend(ABC):
    @abstractmethod
    def format(self, sql: str, dialect: str) -> str:
        raise NotImplementedError


class SqlglotFormatter(FormatterBackend):
    def format(self, sql: str, dialect: str) -> str:
        try:
            expressions = sqlglot.parse(sql, read=dialect)
            formatted = ";\n\n".join(
                expr.sql(dialect=dialect, pretty=True) for expr in expressions
            )
        except Exception as exc:
            raise FormatterError(str(exc)) from exc

        if sql.rstrip().endswith(";") and not formatted.rstrip().endswith(";"):
            formatted += ";"
        return formatted


def get_formatter_backend(backend: str) -> FormatterBackend:
    if backend != "sqlglot":
        raise FormatterError(f"unsupported formatter backend: {backend}")
    return SqlglotFormatter()


def format_sql(sql: str, dialect: str = "redshift", backend: str = "sqlglot") -> str:
    return get_formatter_backend(backend).format(sql.strip(), dialect=dialect)
