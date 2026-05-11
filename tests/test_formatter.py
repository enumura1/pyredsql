import pytest

from pyredsql.errors import FormatterError
from pyredsql.formatter import format_sql


def test_formats_with_clause() -> None:
    sql = """
with base as (
  select user_id, updated_at
  from users
)
select *
from base;
"""

    formatted = format_sql(sql)

    assert "WITH" in formatted
    assert "SELECT" in formatted
    assert formatted.endswith(";")


def test_formats_qualify_without_removing_window_clause() -> None:
    sql = """
select user_id, updated_at
from users
qualify row_number() over(partition by user_id order by updated_at desc)=1;
"""

    formatted = format_sql(sql)

    assert "QUALIFY" in formatted
    assert "ROW_NUMBER" in formatted
    assert "PARTITION BY" in formatted


def test_formats_with_qualify() -> None:
    sql = """
with base as (
  select user_id, updated_at
  from users
)
select *
from base
qualify row_number() over(partition by user_id order by updated_at desc)=1;
"""

    formatted = format_sql(sql)

    assert "WITH" in formatted
    assert "QUALIFY" in formatted
    assert "ROW_NUMBER" in formatted


def test_formats_copy_without_dropping_redshift_clauses() -> None:
    sql = """
COPY users
FROM '<s3-path>'
IAM_ROLE '<iam-role-arn>'
FORMAT AS CSV
IGNOREHEADER 1;
"""

    formatted = format_sql(sql)

    assert "COPY users" in formatted
    assert "IAM_ROLE" in formatted
    assert "IGNOREHEADER 1" in formatted


def test_unload_is_preserved_even_when_sqlglot_uses_command_fallback() -> None:
    sql = """
UNLOAD ('SELECT * FROM users')
TO '<s3-path>'
IAM_ROLE '<iam-role-arn>'
FORMAT AS PARQUET;
"""

    formatted = format_sql(sql)

    assert "UNLOAD" in formatted
    assert "TO '<s3-path>'" in formatted
    assert "FORMAT AS PARQUET" in formatted


def test_unsupported_backend_raises_formatter_error() -> None:
    with pytest.raises(FormatterError):
        format_sql("select * from users", backend="unknown")
