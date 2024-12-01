import sqlite3
from contextlib import contextmanager
from settings.config import log_config, INPUT_IMAGE_FOLDER

import logging, json
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
                       'completed BOOLEAN, last_updated TIMESTAMP, imgs_are_available BOOLEAN, img_total INT, img_processed INT, img_labeled INT DEFAULT (0), label_map TEXT)')
        cursor.execute('CREATE TABLE IF NOT EXISTS image (img_id INTEGER PRIMARY KEY, name TEXT, '
                       'session_id INT, processed BOOLEAN, label TEXT, FOREIGN KEY(session_id) REFERENCES session(session_id))')
        cursor.execute('CREATE TABLE IF NOT EXISTS prediction (pred_id INTEGER PRIMARY KEY, name TEXT, '
                       'label TEXT, processed BOOLEAN, session_id INT, FOREIGN KEY(session_id) REFERENCES session(session_id))')
        cursor.execute('CREATE TABLE IF NOT EXISTS exc_error (exc_error_id INTEGER PRIMARY KEY, session_id INT, traceback TEXT, '
                   'image_path TEXT, timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP, FOREIGN KEY(session_id) REFERENCES session(session_id))')

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
        
def obtain_unlabeled_images_from_session(db_filepath: str, session_id: int) -> list[str]:
    """
    Obtain all unlabeled images from a session.
    """
    with db_ops(db_filepath) as cursor:
        cursor.execute('SELECT name FROM image WHERE session_id=? AND coalesce(label, "") = ""', (session_id,))
        rows = cursor.fetchall()
        img_list = [row[0] for row in rows]
        return img_list
        
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
        cursor.execute('SELECT COUNT(*) FROM image WHERE session_id=? AND processed = true', (session_id,))
        processed_count = cursor.fetchone()[0]
        cursor.execute('SELECT COUNT(*) FROM image WHERE session_id=?', (session_id,))
        total_count = cursor.fetchone()[0]
        cursor.execute('UPDATE session SET img_labeled=?, img_total=?, img_processed=? WHERE session_id=?', (labeled_count, total_count, processed_count, session_id))
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


## For use in image classifier
def get_all_labeled_images(db_filepath: str, session_id: int) -> list[dict]:
    """
    Get all labeled images from a session.
    """
    with db_ops(db_filepath) as cursor:
        cursor.execute("select name as filename, label from image where session_id = ? and label != '';", (session_id,))
        rows = cursor.fetchall()
        data_list = []
        for row in rows:
            data_list.append({'filename': INPUT_IMAGE_FOLDER+'/'+row[0], 'class': row[1]})
        return data_list
    
    
def get_unprocessed_labeled_images(db_filepath: str, session_id: int) -> list[dict]:
    """
    Get only unprocessed labeled images from a session.
    """
    with db_ops(db_filepath) as cursor:
        cursor.execute("select name as filename, label from image where session_id = ? and label != '' and processed = 0;", (session_id,))
        rows = cursor.fetchall()
        data_list = []
        for row in rows:
            data_list.append({'filename': INPUT_IMAGE_FOLDER+'/'+row[0], 'class': row[1]})
        return data_list
    

def set_images_processed(db_filepath: str, session_id: int):    
    """
    Set all labeled images in a session as processed.
    """
    with db_ops(db_filepath) as cursor:
        cursor.execute("UPDATE image SET processed=? WHERE session_id=? and label != '';", (True, session_id))

def save_label_map(db_filepath: str, session_id: int, label_map: dict[int, str]):
    """
    Save the label map in the database.
    """
    json_label_map = json.dumps(label_map)
    with db_ops(db_filepath) as cursor:
        cursor.execute("UPDATE session SET label_map=? WHERE session_id=?", (json_label_map, session_id))

def get_label_map(db_filepath: str, session_id: int) -> dict[int, str]:
    """
    Get the label map from the database.
    """
    with db_ops(db_filepath) as cursor:
        cursor.execute("SELECT label_map FROM session WHERE session_id=?", (session_id,))
        json_label_map = cursor.fetchone()[0]
        if json_label_map is None:
            return None
        label_map = json.loads(json_label_map, object_hook=jsonKeys2int)
        return label_map
    
def jsonKeys2int(x):
    # Should only be used when we are sure that the keys are integers
    if isinstance(x, dict):
        return {int(k):v for k,v in x.items()}
    return x
    
def add_prediction(db_filepath: str, filename: str, label: str, session_id: int):
    """
    Add a new prediction to the database.
    """
    with db_ops(db_filepath) as cursor:
        cursor.execute('INSERT INTO prediction(name, label, session_id, processed) VALUES (?, ?, ?, ?)', (filename, label, session_id, False))

def set_prediction_processed(db_filepath: str, filename: str, session_id: int):
    """
    Set a prediction as processed.
    """
    with db_ops(db_filepath) as cursor:
        cursor.execute('UPDATE prediction SET processed=? WHERE name=? AND session_id=?', (True, filename, session_id))

def get_unprocessed_prediction(db_filepath: str, session_id: int) -> tuple[str, str]:
    """
    Get single unprocessed prediction from the database. The prediction is ordered by label. The group with least labels come first.
    """

    query = '''
            WITH unprocessed_count AS (
                SELECT label, COUNT(*) AS unprocessed_total
                FROM prediction
                WHERE session_id = ? AND processed = 0 AND name IS NOT NULL AND name != ""
                GROUP BY label
                HAVING unprocessed_total > 0
                ORDER BY unprocessed_total ASC
                LIMIT 1
            )
            SELECT name, label
            FROM prediction
            WHERE session_id=? AND processed=? AND name IS NOT NULL AND name != ""
            AND label = (SELECT label FROM unprocessed_count)
            LIMIT 1
            '''
    with db_ops(db_filepath) as cursor:
        cursor.execute(query, (session_id, session_id, False))
        row = cursor.fetchone()
        if row is not None:
            return row[0], row[1] # filename, label
        return None, None
    
def new_exc_error(db_filepath: str, session_id: int, traceback: str, image_path: str = None):
    """
    Add a new exception error to the database.
    """
    with db_ops(db_filepath) as cursor:
        cursor.execute('INSERT INTO exc_error(session_id, traceback, image_path) VALUES (?, ?, ?)', (session_id, traceback, image_path))

def get_errored_images_by_session(db_filepath: str, session_id: int) -> list[dict]:
    """
    Get all exception errors that have an image from a session.
    """
    with db_ops(db_filepath) as cursor:
        cursor.execute('SELECT traceback, image_path, timestamp FROM exc_error WHERE session_id=? AND image_path IS NOT NULL AND image_path != ""', (session_id,))
        rows = cursor.fetchall()
        error_list = [{'traceback': row[0], 'image_path': row[1], 'timestamp': row[2]} for row in rows]
        return error_list