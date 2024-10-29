"""
Functions to interrogate an SQLite database and return the data
"""
import os
from datetime import datetime

import sqlite3


def get_data(path, start=None, end=None, as_datetime=True, select='*'):
    """Fetch all the log records between two dates.

    Parameters
    ----------
    path : :class:`str`
        The path to the SQLite_ database.
    start : :class:`datetime.datetime` or :class:`str`, optional
        Include all records that have a timestamp > `start`. If :class:`str` then in
        ``yyyy-mm-dd`` or ``yyyy-mm-dd HH:MM:SS`` format.
    end : :class:`datetime.datetime` or :class:`str`, optional
        Include all records that have a timestamp < `end`. If :class:`str` then in
        ``yyyy-mm-dd`` or ``yyyy-mm-dd HH:MM:SS`` format.
    as_datetime : :class:`bool`, optional
        Whether to fetch the timestamps from the database as :class:`datetime.datetime` objects.
        If :data:`False` then the timestamps will be of type :class:`str` and this function
        will return much faster if requesting data over a large date range.
    select : :class:`str` or :class:`list` of :class:`str`, optional
        The column(s) in the database to use with the ``SELECT`` SQL command.

    Returns
    -------
    :class:`list` of :class:`tuple`
        A list of ``(timestamp, resistance, ...)`` log records,
        depending on the value of `select`.
    """
    if not os.path.isfile(path):
        raise IOError('Cannot find {}'.format(path))

    detect_types = sqlite3.PARSE_DECLTYPES | sqlite3.PARSE_COLNAMES if as_datetime else 0
    db = sqlite3.connect(path, timeout=10.0, detect_types=detect_types,
                         isolation_level=None)  # Open database in Autocommit mode by setting isolation_level to None
    db.execute(
        'pragma journal_mode=wal')  # Set sqlite to Write-Ahead Log (WAL) journal mode to allow concurrent read and write connection to the database
    cursor = db.cursor()

    if isinstance(start, datetime):
        start = start.isoformat(sep='T')
    if isinstance(end, datetime):
        end = end.isoformat(sep='T')
    if select != '*':
        if isinstance(select, (list, tuple, set)):
            select = ','.join(select)
    base = 'SELECT {} FROM data'.format(select)

    if start is None and end is None:
        cursor.execute(base + ';')
    elif start is not None and end is None:
        cursor.execute(base + ' WHERE datetime > ?;', (start,))
    elif start is None and end is not None:
        cursor.execute(base + ' WHERE datetime < ?;', (end,))
    else:
        cursor.execute(base + ' WHERE datetime BETWEEN ? AND ?;', (start, end))

    data = cursor.fetchall()
    cursor.close()
    db.close()

    return data
