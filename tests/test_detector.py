from pathlib import Path

from pyredsql.detector import detect_sql_blocks


def test_detects_triple_quoted_query_assignment() -> None:
    source = '''query = """
select * from users
"""
'''

    blocks = detect_sql_blocks(Path("foo.py"), source)

    assert len(blocks) == 1
    assert blocks[0].variable_name == "query"
    assert blocks[0].confidence == 0.95
    assert blocks[0].raw_sql.strip() == "select * from users"


def test_detects_sql_suffix_variable() -> None:
    source = '''load_users_sql = """
select * from users
"""
'''

    blocks = detect_sql_blocks(Path("foo.py"), source)

    assert len(blocks) == 1
    assert blocks[0].variable_name == "load_users_sql"


def test_detects_single_quote_triple_string() -> None:
    source = """sql = '''
select * from users
'''
"""

    blocks = detect_sql_blocks(Path("foo.py"), source)

    assert len(blocks) == 1
    assert blocks[0].quote == "'''"


def test_marks_f_string_as_unsafe() -> None:
    source = '''query = f"""
select * from users where id = {user_id}
"""
'''

    blocks = detect_sql_blocks(Path("foo.py"), source)

    assert len(blocks) == 1
    assert blocks[0].is_f_string is True


def test_marks_jinja_like_sql() -> None:
    source = '''query = """
select * from users where ds = '{{ ds }}'
"""
'''

    blocks = detect_sql_blocks(Path("foo.py"), source)

    assert len(blocks) == 1
    assert blocks[0].has_jinja is True
