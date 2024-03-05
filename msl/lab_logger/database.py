from enum import Enum
import os
import sqlite3
from typing import TypeVar, Sequence

from msl.equipment import Config

from .sensors import Sensor


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

    def __init__(self, cfg: Config, sensor: Sensor) -> None:
        """
        Initialise two tables: one for data and one for metadata
        """
        self.path = os.path.join(cfg.value('log_dir'), f'{sensor.record.serial}.sqlite3')
        self.timeout = cfg.value('db_timeout', 10)

        db = sqlite3.connect(self.path, timeout=self.timeout)
        # Set sqlite to Write-Ahead Log (WAL) journal mode to allow concurrent read and write connection to the database
        db.execute('pragma journal_mode=wal')

        #  data
        field_str = ', '.join(f'{k} {v.name}' for k, v in sensor.fields.items())
        db.execute(
            f'CREATE TABLE IF NOT EXISTS data ('
            f'pid INTEGER PRIMARY KEY AUTOINCREMENT, '
            f'datetime DATETIME, '
            f'{field_str}'
            f')'
        )
        #  metadata - e.g. a place to store the equipment record for the source of the logged data
        db.execute(f'CREATE TABLE IF NOT EXISTS metadata (field TEXT, value TEXT)')

        # TODO: determine the best way to represent the equipment record
        # metadata_dict = sensor.record.to_dict()
        # for k, v in metadata_dict.items():
        data = ('model', sensor.record.model)
        db.execute(f'INSERT INTO metadata VALUES (?, ?);', data)
        db.commit()

    def write(self, data: Sequence[float]) -> None:
        """
        write data to the database
        """
        questions = ', '.join('?' for _ in data)
        with sqlite3.connect(self.path, timeout=self.timeout) as db:
            db.execute(f'INSERT INTO data VALUES (NULL, {questions});', data)
            db.commit()
