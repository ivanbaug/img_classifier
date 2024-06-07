import sqlite3
from contextlib import contextmanager
from settings.config import log_config

import logging
from logging import config as logging_config
logging_config.dictConfig(log_config)
logger = logging.getLogger()

@contextmanager
def db_ops(db_filepath: str):
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

def initialize_db(db_filepath: str) -> None:
    """
    Creates a connection to the database and creates the tables if they don't exist.
    """
    with db_ops(db_filepath) as cursor:
        cursor.execute('CREATE TABLE IF NOT EXISTS image (name TEXT, session INT, processed BOOLEAN, '
                       'classification TEXT)')
        logger.info('Database initialized')

def get_new_session_id(db_filepath: str) -> int:
    """
    Get the next session id.
    """
    with db_ops(db_filepath) as cursor:
        cursor.execute('SELECT MAX(session) FROM image')
        session_id = cursor.fetchone()[0]
        if session_id is None:
            session_id = 0
        else:
            session_id += 1
        logger.info(f'New session id: {session_id}')
        return session_id
    
def initialize_images_session(db_filepath: str, images: list[str], session_id: int):
    """
    Initialize the images in database for the session.
    """
    with db_ops(db_filepath) as cursor:
        img_array = [(i, session_id, False, '') for i in images]
        cursor.executemany('INSERT INTO image(name, session, processed, classification) '
                           'VALUES (?, ?, ?, ?)', img_array)
        logger.info(f'Images initialized for session: {session_id}')

def obtain_random_unprocessed_image(db_filepath: str, session_id: int) -> str:
    """
    Obtain a random unprocessed image.
    """
    query = '''SELECT name FROM image WHERE rowid IN 
            (SELECT rowid FROM image WHERE session=? AND processed=? ORDER BY RANDOM() LIMIT 1)'''
    with db_ops(db_filepath) as cursor:
        cursor.execute(query, (session_id, False))
        image = cursor.fetchone()
        print(image)
        if image is not None:
            logger.info(f'Random image obtained: {image[0]}')
            return image[0]
        else:
            logger.info('No unprocessed images found')
            return ''
        
def update_image_classification(db_filepath: str, session_id: int, filename: str, classification: str):
    """
    Update the classification of an image.
    """
    with db_ops(db_filepath) as cursor:
        cursor.execute('UPDATE image SET classification=?, processed=? WHERE name=? AND session=?',
                       (classification, True, filename, session_id))