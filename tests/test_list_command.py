from typer.testing import CliRunner

from pyredsql.cli import app

runner = CliRunner()


def test_list_command_prints_detected_blocks(tmp_path) -> None:
    file = tmp_path / "foo.py"
    file.write_text(
        '''query = """
select * from users
"""
''',
        encoding="utf-8",
    )

    result = runner.invoke(app, ["list", str(file)])

    assert result.exit_code == 0, result.output
    assert "Found 1 SQL blocks" in result.output
    assert "variable: query" in result.output
