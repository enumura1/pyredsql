from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class SqlBlock:
    file_path: Path
    start_line: int
    end_line: int
    start_col: int
    end_col: int
    variable_name: str | None
    raw_sql: str
    quote: str
    prefix: str
    is_f_string: bool
    has_jinja: bool
    confidence: float
