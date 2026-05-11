from __future__ import annotations

import difflib
from pathlib import Path
from typing import Annotated

import typer
from rich.console import Console

from pyredsql.detector import detect_sql_blocks
from pyredsql.errors import FormatterError
from pyredsql.extractor import build_sql_file_name, write_sql_file_at_path
from pyredsql.formatter import format_sql
from pyredsql.models import SqlBlock
from pyredsql.rewriter import replace_sql_block_with_reference, replace_sql_content

app = typer.Typer(no_args_is_help=True)
console = Console()


@app.command("list")
def list_blocks(file: Annotated[Path, typer.Argument(exists=True, dir_okay=False)]) -> None:
    source = file.read_text(encoding="utf-8")
    blocks = detect_sql_blocks(file, source)
    if not blocks:
        console.print("No embedded SQL blocks found.")
        return

    console.print(f"Found {len(blocks)} SQL blocks")
    for number, block in enumerate(blocks, start=1):
        console.print()
        console.print(f"{number}. {block.file_path}:{block.start_line}-{block.end_line}")
        console.print(f"   variable: {block.variable_name or '-'}")
        console.print(f"   confidence: {block.confidence:.2f}")
        console.print(f"   unsafe: {str(_is_unsafe(block)).lower()}")


@app.command("format")
def format_command(
    file: Annotated[Path, typer.Argument(exists=True, dir_okay=False)],
    dialect: Annotated[str, typer.Option()] = "redshift",
    backend: Annotated[str, typer.Option()] = "sqlglot",
    write: Annotated[bool, typer.Option("--write/--check")] = True,
    dry_run: Annotated[bool, typer.Option("--dry-run")] = False,
    include_unsafe: Annotated[bool, typer.Option("--include-unsafe")] = False,
) -> None:
    source = file.read_text(encoding="utf-8")
    blocks = detect_sql_blocks(file, source)
    if not blocks:
        console.print("No embedded SQL blocks found.")
        raise typer.Exit(0)

    new_source, warnings = _format_source(
        source,
        blocks,
        dialect=dialect,
        backend=backend,
        include_unsafe=include_unsafe,
    )
    for warning in warnings:
        console.print(f"Warning: {warning}")

    changed = new_source != source
    if dry_run:
        _print_diff(file, source, new_source)
        raise typer.Exit(1 if not write and changed else 0)
    if not write:
        if changed:
            console.print("Found unformatted embedded SQL:")
            for block in blocks:
                console.print(
                    f"- {block.file_path}:{block.start_line}-{block.end_line} "
                    f"variable={block.variable_name or '-'}"
                )
            raise typer.Exit(1)
        raise typer.Exit(0)

    if changed:
        file.write_text(new_source, encoding="utf-8")
        console.print(f"Formatted {file}")


@app.command("check")
def check_command(
    file: Annotated[Path, typer.Argument(exists=True, dir_okay=False)],
    dialect: Annotated[str, typer.Option()] = "redshift",
    backend: Annotated[str, typer.Option()] = "sqlglot",
) -> None:
    format_command(file, dialect=dialect, backend=backend, write=False, dry_run=False)


@app.command("extract")
def extract_command(
    file: Annotated[Path, typer.Argument(exists=True, dir_okay=False)],
    out_dir: Annotated[Path, typer.Option("--out-dir")] = Path("sql"),
    dialect: Annotated[str, typer.Option()] = "redshift",
    backend: Annotated[str, typer.Option()] = "sqlglot",
    replace_mode: Annotated[str, typer.Option("--replace-mode")] = "path",
    dry_run: Annotated[bool, typer.Option("--dry-run")] = False,
    name: Annotated[str | None, typer.Option("--name")] = None,
) -> None:
    source = file.read_text(encoding="utf-8")
    blocks = detect_sql_blocks(file, source)
    if not blocks:
        console.print("No embedded SQL blocks found.")
        raise typer.Exit(0)
    if name and len(blocks) > 1:
        console.print("Error: --name can only be used when exactly one SQL block is detected.")
        raise typer.Exit(1)

    out_dir = out_dir if out_dir.is_absolute() else file.parent / out_dir
    replacements: list[tuple[SqlBlock, Path, str]] = []
    planned_paths: set[Path] = set()
    for block in blocks:
        if block.is_f_string:
            console.print(
                f"Skipped unsafe SQL block {file}:{block.start_line}-{block.end_line} "
                "reason=f-string"
            )
            continue

        file_name = f"{name}.sql" if name else build_sql_file_name(block, file)
        output_path = _unique_planned_sql_path(out_dir, file_name, planned_paths)
        planned_paths.add(output_path)
        sql = block.raw_sql.strip()
        if not block.has_jinja:
            try:
                sql = format_sql(sql, dialect=dialect, backend=backend)
            except FormatterError:
                console.print(
                    "Warning: failed to format SQL block "
                    f"{file}:{block.start_line}-{block.end_line} with {backend}. "
                    "Writing original SQL."
                )
        replacements.append((block, output_path, sql))

    if not replacements:
        raise typer.Exit(0)

    new_source = source
    for block, output_path, _sql in reversed(replacements):
        reference = output_path.relative_to(file.parent).as_posix()
        new_source = replace_sql_block_with_reference(
            new_source, block, reference, replace_mode=replace_mode
        )

    if dry_run:
        for _block, output_path, _sql in replacements:
            console.print(f"Would write {output_path}")
        _print_diff(file, source, new_source)
        raise typer.Exit(0)

    for _block, output_path, sql in replacements:
        write_sql_file_at_path(output_path, sql)
        console.print(f"Wrote {output_path}")

    file.write_text(new_source, encoding="utf-8")
    if replace_mode == "read-text":
        console.print("Warning: replace-mode=read-text requires `from pathlib import Path`.")


def _format_source(
    source: str,
    blocks: list[SqlBlock],
    dialect: str,
    backend: str,
    include_unsafe: bool,
) -> tuple[str, list[str]]:
    warnings: list[str] = []
    new_source = source
    for block in reversed(blocks):
        reason = _unsafe_reason(block)
        if reason and not include_unsafe:
            warnings.append(
                f"Skipped unsafe SQL block {block.file_path}:{block.start_line}-"
                f"{block.end_line} reason={reason}"
            )
            continue
        try:
            formatted = format_sql(block.raw_sql, dialect=dialect, backend=backend)
        except FormatterError:
            warnings.append(
                f"failed to format SQL block {block.file_path}:{block.start_line}-"
                f"{block.end_line} with {backend}. Skipping."
            )
            continue
        new_source = replace_sql_content(new_source, block, formatted)
    return new_source, warnings


def _unsafe_reason(block: SqlBlock) -> str | None:
    if block.is_f_string:
        return "f-string"
    if block.has_jinja:
        return "jinja"
    return None


def _is_unsafe(block: SqlBlock) -> bool:
    return _unsafe_reason(block) is not None


def _print_diff(file: Path, old: str, new: str) -> None:
    if old == new:
        console.print("No changes.")
        return
    diff = difflib.unified_diff(
        old.splitlines(),
        new.splitlines(),
        fromfile=str(file),
        tofile=str(file),
        lineterm="",
    )
    console.print("\n".join(diff))


def _unique_planned_sql_path(out_dir: Path, file_name: str, planned_paths: set[Path]) -> Path:
    normalized_name = file_name if file_name.endswith(".sql") else f"{file_name}.sql"
    candidate = out_dir / normalized_name
    if not candidate.exists() and candidate not in planned_paths:
        return candidate

    stem = candidate.stem
    suffix = candidate.suffix
    counter = 2
    while True:
        numbered = out_dir / f"{stem}_{counter}{suffix}"
        if not numbered.exists() and numbered not in planned_paths:
            return numbered
        counter += 1
