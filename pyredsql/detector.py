from __future__ import annotations

import io
import re
import tokenize
from pathlib import Path
from tokenize import TokenInfo

from pyredsql.models import SqlBlock

SQL_KEYWORDS = (
    "SELECT",
    "WITH",
    "INSERT",
    "UPDATE",
    "DELETE",
    "CREATE",
    "ALTER",
    "DROP",
    "COPY",
    "UNLOAD",
    "QUALIFY",
    "MERGE",
    "FROM",
    "JOIN",
    "WHERE",
    "GROUP BY",
    "ORDER BY",
)

REDSHIFT_KEYWORDS = (
    "QUALIFY",
    "COPY",
    "UNLOAD",
    "DISTKEY",
    "SORTKEY",
    "DISTSTYLE",
    "ENCODE",
    "IAM_ROLE",
)

SQL_VARIABLE_RE = re.compile(r"^(sql|query|.*_sql|.*_query)$")
TRIPLE_STRING_RE = re.compile(
    r"(?is)^(?P<prefix>[rubf]*)?(?P<quote>'''|\"\"\")(?P<body>.*)(?P=quote)$"
)


def detect_sql_blocks(file_path: Path, source: str) -> list[SqlBlock]:
    tokens = list(tokenize.generate_tokens(io.StringIO(source).readline))
    blocks: list[SqlBlock] = []
    lines = source.splitlines(keepends=True)

    for index, token in enumerate(tokens):
        if token.type == getattr(tokenize, "FSTRING_START", -1):
            parsed_f_string = _parse_triple_f_string_start(token.string)
            if parsed_f_string is None:
                continue

            end_index = _find_f_string_end(tokens, index)
            if end_index is None:
                continue

            prefix, quote = parsed_f_string
            end_token = tokens[end_index]
            raw_sql = _slice_source(lines, token.end, end_token.start)
            variable_name = _find_assigned_variable(tokens, index)
            confidence = _confidence(raw_sql, variable_name)
            if confidence < 0.7:
                continue

            blocks.append(
                SqlBlock(
                    file_path=file_path,
                    start_line=token.start[0],
                    end_line=end_token.end[0],
                    start_col=token.start[1],
                    end_col=end_token.end[1],
                    variable_name=variable_name,
                    raw_sql=raw_sql,
                    quote=quote,
                    prefix=prefix,
                    is_f_string=True,
                    has_jinja="{{" in raw_sql or "{%" in raw_sql,
                    confidence=confidence,
                )
            )
            continue

        if token.type != tokenize.STRING:
            continue

        parsed = _parse_triple_string_token(token.string)
        if parsed is None:
            continue

        prefix, quote, raw_sql = parsed
        variable_name = _find_assigned_variable(tokens, index)
        confidence = _confidence(raw_sql, variable_name)
        if confidence < 0.7:
            continue

        lower_prefix = prefix.lower()
        blocks.append(
            SqlBlock(
                file_path=file_path,
                start_line=token.start[0],
                end_line=token.end[0],
                start_col=token.start[1],
                end_col=token.end[1],
                variable_name=variable_name,
                raw_sql=raw_sql,
                quote=quote,
                prefix=prefix,
                is_f_string="f" in lower_prefix,
                has_jinja="{{" in raw_sql or "{%" in raw_sql,
                confidence=confidence,
            )
        )

    return blocks


def _parse_triple_string_token(token_string: str) -> tuple[str, str, str] | None:
    match = TRIPLE_STRING_RE.match(token_string)
    if match is None:
        return None
    prefix = match.group("prefix") or ""
    if "b" in prefix.lower():
        return None
    return prefix, match.group("quote"), match.group("body")


def _parse_triple_f_string_start(token_string: str) -> tuple[str, str] | None:
    match = re.match(r"(?is)^(?P<prefix>[rubf]*)(?P<quote>'''|\"\"\")$", token_string)
    if match is None:
        return None
    return match.group("prefix"), match.group("quote")


def _find_f_string_end(tokens: list[TokenInfo], start_index: int) -> int | None:
    end_type = getattr(tokenize, "FSTRING_END", -1)
    for index in range(start_index + 1, len(tokens)):
        if tokens[index].type == end_type:
            return index
    return None


def _slice_source(
    lines: list[str],
    start: tuple[int, int],
    end: tuple[int, int],
) -> str:
    start_offset = sum(len(line) for line in lines[: start[0] - 1]) + start[1]
    end_offset = sum(len(line) for line in lines[: end[0] - 1]) + end[1]
    return "".join(lines)[start_offset:end_offset]


def _find_assigned_variable(tokens: list[TokenInfo], string_index: int) -> str | None:
    line_tokens: list[TokenInfo] = []
    for token in reversed(tokens[:string_index]):
        if token.type in {tokenize.NEWLINE, tokenize.NL, tokenize.INDENT, tokenize.DEDENT}:
            break
        if token.type != tokenize.COMMENT:
            line_tokens.append(token)
    line_tokens.reverse()

    equals_index = next(
        (i for i, token in enumerate(line_tokens) if token.string == "="),
        None,
    )
    if equals_index is None:
        return None

    lhs = line_tokens[:equals_index]
    names = [token.string for token in lhs if token.type == tokenize.NAME]
    if not names:
        return None
    return names[0]


def _confidence(sql: str, variable_name: str | None) -> float:
    upper_sql = sql.upper()
    has_sql_variable = bool(variable_name and SQL_VARIABLE_RE.match(variable_name))
    keyword_count = sum(1 for keyword in SQL_KEYWORDS if keyword in upper_sql)
    has_redshift_keyword = any(keyword in upper_sql for keyword in REDSHIFT_KEYWORDS)

    if has_redshift_keyword:
        return 0.95
    if has_sql_variable and keyword_count:
        return 0.95
    if "SELECT" in upper_sql and "FROM" in upper_sql:
        return 0.8
    if keyword_count >= 2:
        return 0.75
    if has_sql_variable and keyword_count:
        return 0.7
    return 0.5
