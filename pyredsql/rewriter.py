from __future__ import annotations

from pyredsql.models import SqlBlock


def replace_sql_content(source: str, block: SqlBlock, new_sql: str) -> str:
    token_text = block.prefix + block.quote + _string_body(new_sql) + block.quote
    return _replace_range(source, block, token_text)


def replace_sql_block_with_reference(
    source: str,
    block: SqlBlock,
    reference: str,
    replace_mode: str,
) -> str:
    if replace_mode == "path":
        replacement = _python_double_quoted_string(reference)
    elif replace_mode == "read-text":
        replacement = f"Path({_python_double_quoted_string(reference)}).read_text()"
    else:
        raise ValueError(f"unsupported replace mode: {replace_mode}")
    return _replace_range(source, block, replacement)


def _string_body(sql: str) -> str:
    sql = sql.strip("\n")
    return f"\n{sql}\n"


def _replace_range(source: str, block: SqlBlock, replacement: str) -> str:
    lines = source.splitlines(keepends=True)
    start_offset = sum(len(line) for line in lines[: block.start_line - 1]) + block.start_col
    end_offset = sum(len(line) for line in lines[: block.end_line - 1]) + block.end_col
    return source[:start_offset] + replacement + source[end_offset:]


def _python_double_quoted_string(value: str) -> str:
    escaped = value.replace("\\", "\\\\").replace('"', '\\"')
    return f'"{escaped}"'
