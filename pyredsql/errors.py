class PyredsqlError(Exception):
    """Base error for pyredsql."""


class FormatterError(PyredsqlError):
    """Raised when a formatter backend cannot format a SQL block."""
