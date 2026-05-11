from typer.testing import CliRunner

from pyredsql.cli import app

runner = CliRunner()


def test_format_command_rewrites_embedded_sql(tmp_path) -> None:
    file = tmp_path / "foo.py"
    file.write_text(
        '''query = """
select user_id, updated_at
from users
qualify row_number() over(partition by user_id order by updated_at desc)=1
"""
''',
        encoding="utf-8",
    )

    result = runner.invoke(app, ["format", str(file)])

    assert result.exit_code == 0, result.output
    source = file.read_text(encoding="utf-8")
    assert "SELECT" in source
    assert "QUALIFY" in source
    assert "ROW_NUMBER" in source
    assert "PARTITION BY" in source


def test_format_dry_run_does_not_modify_file(tmp_path) -> None:
    file = tmp_path / "foo.py"
    original = '''query = """
select * from users
"""
'''
    file.write_text(original, encoding="utf-8")

    result = runner.invoke(app, ["format", str(file), "--dry-run"])

    assert result.exit_code == 0, result.output
    assert file.read_text(encoding="utf-8") == original
    assert "SELECT" in result.output


def test_check_returns_one_for_unformatted_sql(tmp_path) -> None:
    file = tmp_path / "foo.py"
    file.write_text(
        '''query = """
select * from users
"""
''',
        encoding="utf-8",
    )

    result = runner.invoke(app, ["check", str(file)])

    assert result.exit_code == 1
    assert "Found unformatted embedded SQL" in result.output


def test_format_skips_jinja_sql(tmp_path) -> None:
    file = tmp_path / "foo.py"
    original = '''query = """
select * from users where ds = '{{ ds }}'
"""
'''
    file.write_text(original, encoding="utf-8")

    result = runner.invoke(app, ["format", str(file)])

    assert result.exit_code == 0, result.output
    assert file.read_text(encoding="utf-8") == original
    assert "reason=jinja" in result.output
