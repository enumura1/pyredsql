# pyredsql

Format and extract Redshift SQL embedded in Python files.

pyredsql is a Redshift-first CLI tool for refactoring SQL strings in Python.
It can format embedded SQL and extract it into external `.sql` files.

pyredsql is an early MVP. It uses SQLGlot internally for best-effort SQL
formatting and currently targets Python triple-quoted strings. Unsafe blocks,
including f-strings and Jinja-like templates, are skipped by default.

pyredsql does not connect to databases and does not execute SQL.

## Install

```bash
pip install pyredsql
```

```bash
pipx install pyredsql
```

```bash
uvx pyredsql --help
```

## Format embedded Redshift SQL

```bash
pyredsql format jobs/load_users.py
```

## Extract embedded SQL to file

```bash
pyredsql extract jobs/load_users.py --out-dir sql
```

## Why?

Existing SQL formatters work well on `.sql` files, but many real-world Python projects contain large embedded SQL strings.
pyredsql helps migrate those SQL strings into external `.sql` files safely.
