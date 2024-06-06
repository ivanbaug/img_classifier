import sqlite3
from contextlib import contextmanager
from settings.config import log_config

import logging
from logging import config as logging_config
logging_config.dictConfig(log_config)
logger = logging.getLogger()

@contextmanager
def db_ops(db_filepath):
    try:
        conn = sqlite3.connect(db_filepath, detect_types=sqlite3.PARSE_DECLTYPES | sqlite3.PARSE_COLNAMES)
        cursor = conn.cursor()
        yield cursor
        conn.commit()
    except Exception as _:
        logger.error('Exception while performing db operation', exc_info=True)
        raise
    finally:
        cursor.close()
        conn.close()

def initialize_db(db_filepath) -> None:
    """
    Creates a connection to the database and creates the tables if they don't exist.
    """
    with db_ops(db_filepath) as cursor:
        cursor.execute('CREATE TABLE IF NOT EXISTS image (name TEXT, session INT, processed BOOLEAN, '
                       'classification TEXT)')
        logger.info('Database initialized')