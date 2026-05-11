from typer.testing import CliRunner

from pyredsql.cli import app

runner = CliRunner()


def test_extract_writes_sql_file_and_replaces_python_string(tmp_path) -> None:
    file = tmp_path / "foo.py"
    file.write_text(
        '''query = """
select * from users
"""
''',
        encoding="utf-8",
    )

    result = runner.invoke(app, ["extract", str(file), "--out-dir", "sql"])

    assert result.exit_code == 0, result.output
    sql_file = tmp_path / "sql" / "query.sql"
    assert sql_file.exists()
    assert "SELECT" in sql_file.read_text(encoding="utf-8")
    assert file.read_text(encoding="utf-8") == 'query = "sql/query.sql"\n'


def test_extract_dry_run_does_not_modify_files(tmp_path) -> None:
    file = tmp_path / "foo.py"
    original = '''query = """
select * from users
"""
'''
    file.write_text(original, encoding="utf-8")

    result = runner.invoke(app, ["extract", str(file), "--out-dir", "sql", "--dry-run"])

    assert result.exit_code == 0, result.output
    assert file.read_text(encoding="utf-8") == original
    assert not (tmp_path / "sql").exists()
    assert "Would write" in result.output


def test_extract_read_text_mode(tmp_path) -> None:
    file = tmp_path / "foo.py"
    file.write_text(
        '''query = """
select * from users
"""
''',
        encoding="utf-8",
    )

    result = runner.invoke(
        app,
        ["extract", str(file), "--out-dir", "sql", "--replace-mode", "read-text"],
    )

    assert result.exit_code == 0, result.output
    assert file.read_text(encoding="utf-8") == 'query = Path("sql/query.sql").read_text()\n'
    assert "requires `from pathlib import Path`" in result.output


def test_extract_avoids_name_collisions_within_same_run(tmp_path) -> None:
    file = tmp_path / "foo.py"
    file.write_text(
        '''query = """
select * from users
"""

query = """
select * from events
"""
''',
        encoding="utf-8",
    )

    result = runner.invoke(app, ["extract", str(file), "--out-dir", "sql"])

    assert result.exit_code == 0, result.output
    assert (tmp_path / "sql" / "query.sql").exists()
    assert (tmp_path / "sql" / "query_2.sql").exists()
    assert file.read_text(encoding="utf-8") == (
        'query = "sql/query.sql"\n'
        "\n"
        'query = "sql/query_2.sql"\n'
    )
