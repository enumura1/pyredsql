from __future__ import annotations

from pathlib import Path

from pyredsql.models import SqlBlock


def build_sql_file_name(block: SqlBlock, source_file: Path) -> str:
    if block.variable_name:
        stem = block.variable_name
        for suffix in ("_sql", "_query"):
            if stem.endswith(suffix):
                stem = stem[: -len(suffix)]
                break
        return f"{stem}.sql"
    return f"{source_file.stem}_l{block.start_line}.sql"


def unique_sql_path(out_dir: Path, file_name: str) -> Path:
    candidate = out_dir / _ensure_sql_suffix(file_name)
    if not candidate.exists():
        return candidate

    stem = candidate.stem
    suffix = candidate.suffix
    counter = 2
    while True:
        numbered = out_dir / f"{stem}_{counter}{suffix}"
        if not numbered.exists():
            return numbered
        counter += 1


def write_sql_file(out_dir: Path, file_name: str, sql: str) -> Path:
    out_dir.mkdir(parents=True, exist_ok=True)
    path = unique_sql_path(out_dir, file_name)
    write_sql_file_at_path(path, sql)
    return path


def write_sql_file_at_path(path: Path, sql: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(_ensure_trailing_newline(sql), encoding="utf-8")


def _ensure_sql_suffix(file_name: str) -> str:
    return file_name if file_name.endswith(".sql") else f"{file_name}.sql"


def _ensure_trailing_newline(sql: str) -> str:
    return sql if sql.endswith("\n") else f"{sql}\n"
