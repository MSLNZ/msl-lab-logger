from enum import Enum


class DatabaseTypes(Enum):
    """SQLite data types."""
    NULL = 'NULL'
    INTEGER = 'INTEGER'
    REAL = 'REAL'
    TEXT = 'TEXT'
    BLOB = 'BLOB'
    DATETIME = 'DATETIME'
    FLOAT = 'REAL'


class Database:

    def __init__(self, path: str, fields: dict) -> None:
        # Initialize 2 tables (if they don't already exist)
        #  data
        #  metadata
        pass

    def read(self):
        pass

    def write(self, *data) -> None:
        # get timestamp
        # autoincrement ID
        pass

