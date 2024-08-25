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
        cursor.execute('CREATE TABLE IF NOT EXISTS session (session_id INTEGER PRIMARY KEY, '
                       'completed BOOLEAN, last_updated TIMESTAMP, imgs_are_available BOOLEAN, img_total INT, img_processed INT, img_labeled INT DEFAULT (0))')
        cursor.execute('CREATE TABLE IF NOT EXISTS image (img_id INTEGER PRIMARY KEY, name TEXT, '
                       'session_id INT, processed BOOLEAN, label TEXT, FOREIGN KEY(session_id) REFERENCES session(session_id))')
        logger.info('Database initialized')

# TODO: Remove if not used
def get_new_session_id(db_filepath: str) -> int:
    """
    Get the next session id.
    """
    with db_ops(db_filepath) as cursor:
        cursor.execute('SELECT MAX(session_id) FROM image')
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
        cursor.executemany('INSERT INTO image(name, session_id, processed, label) '
                           'VALUES (?, ?, ?, ?)', img_array)
        logger.info(f'Images initialized for session: {session_id}')

def obtain_random_unlabeled_image(db_filepath: str, session_id: int) -> str:
    """
    Obtain a random unlabeled image.
    """
    query = '''SELECT name FROM image WHERE img_id IN 
            (SELECT img_id FROM image WHERE session_id=? AND coalesce(label, '') = '' ORDER BY RANDOM() LIMIT 1)'''
    with db_ops(db_filepath) as cursor:
        cursor.execute(query, (session_id,))
        image = cursor.fetchone()
        print(image)
        if image is not None:
            logger.info(f'Random image obtained: {image[0]}')
            return image[0]
        else:
            logger.info('No unlabeled images found')
            return ''
        
def update_image_label(db_filepath: str, session_id: int, filename: str, label: str):
    """
    Update the label of an image.
    """
    with db_ops(db_filepath) as cursor:
        cursor.execute('UPDATE image SET label=? WHERE name=? AND session_id=?',
                       (label, filename, session_id))

def update_session_labeled_count(db_filepath: str, session_id: int):
    """
    Update the count of labeled images in a session.
    """
    with db_ops(db_filepath) as cursor:
        cursor.execute("SELECT COUNT(*) FROM image WHERE session_id=? AND not coalesce(label, '') = ''", (session_id,))
        labeled_count = cursor.fetchone()[0]
        cursor.execute('SELECT COUNT(*) FROM image WHERE session_id=?', (session_id))
        total_count = cursor.fetchone()[0]
        cursor.execute('UPDATE session SET img_labeled=?, img_total=? WHERE session_id=?', (labeled_count, total_count, session_id))
        return labeled_count, total_count

def get_sessions(db_filepath: str, **kwargs) -> list[dict]:
    """
    Get the sessions from the database. 
    """
    base_query = 'SELECT * FROM session'
    if kwargs:
        query = base_query + ' WHERE '
        query += ' AND '.join([f'{key}={value}' for key, value in kwargs.items()])
    else:
        query = base_query

    with db_ops(db_filepath) as cursor:
        cursor.execute(query)
        rows = cursor.fetchall()
        session_list = []
        for row in rows:
            session_list.append( { 'session_id':row[0], 'completed': row[1] > 0, 'last_updated': row[2], 'imgs_are_available': row[3] > 0, 'img_total': row[4], 'img_processed': row[5], 'img_labeled': row[6]})
        return session_list
    
def get_img_names_from_session(db_filepath: str, session_id: int) -> list[str]:
    """
    Get the names of the images from a session.
    """
    with db_ops(db_filepath) as cursor:
        cursor.execute('SELECT name FROM image WHERE session_id=?', (session_id,))
        rows = cursor.fetchall()
        img_list = [row[0] for row in rows]
        return img_list
    
def get_imgs_from_session(db_filepath: str, session_id: int) -> list[str]:
    """
    Get the images and its data from a session.
    """
    with db_ops(db_filepath) as cursor:
        cursor.execute('SELECT img_id, name, session_id, processed, label FROM image WHERE session_id=?', (session_id,))
        rows = cursor.fetchall()
        img_data_list = [ { 'img_id': row[0], 'name': row[1], 'session_id': row[2], 'processed': row[3] > 0, 'label': row[4]} for row in rows]
        return img_data_list
    
def get_image_classes(db_filepath: str, session_id: int) -> list[str]:
    """
    Get the classes of the images from a session.
    """
    with db_ops(db_filepath) as cursor:
        cursor.execute('SELECT DISTINCT label FROM image WHERE session_id=?', (session_id,))
        rows = cursor.fetchall()
        class_list = [row[0] for row in rows]
        return class_list
    
def new_session(db_filepath: str, img_total: int, img_processed: int, img_available: bool = False, img_labeled: int = 0) -> int:
    """
    Create a new session in the database.
    """
    with db_ops(db_filepath) as cursor:
        cursor.execute('INSERT INTO session(completed, last_updated, imgs_are_available, img_total, img_processed, img_labeled) '
                       'VALUES (?, CURRENT_TIMESTAMP, ?, ?, ?, ?)', (False, img_available, img_total, img_processed, img_labeled))
        session_id = cursor.lastrowid
        # logger.info(f'New session created: {session_id}')
    return session_id

def set_not_available(db_filepath: str):
    """
    Set all images to not available. Since we are going to evaluate availability of images in the folder.
    """
    with db_ops(db_filepath) as cursor:
        cursor.execute('UPDATE session SET imgs_are_available=?', (False,))

def set_session_imgs_available(db_filepath: str, session_id: int):
    """
    Set the images in a session to available.
    """
    with db_ops(db_filepath) as cursor:
        cursor.execute('UPDATE session SET imgs_are_available=? WHERE session_id=?', (True, session_id))

def get_stats_from_session(db_filepath: str, session_id: int) -> dict:
    """
    Get the stats from a session.
    """
    with db_ops(db_filepath) as cursor:
        cursor.execute("select label as img_class, sum(1) as img_amount  from image where image.session_id = ? group by label;", (session_id,))
        rows = cursor.fetchall()
        r = []
        for row in rows:
            r.append({'class': row[0], 'amount': row[1]})
        return r

