from dotenv import load_dotenv
import os

load_dotenv()  # take environment variables from .env

PRODUCTION = os.getenv('PRODUCTION') == 'True'

if PRODUCTION:
    VOLUME_PATH = os.getenv('VOLUME_PATH')
else:
    VOLUME_PATH = ''

logging_file = VOLUME_PATH + 'app.log'
db_file = VOLUME_PATH + 'db.sqlite3'

IMAGE_FOLDER = VOLUME_PATH + 'static/images'

# Nice guide to logging config with dictionary
# https://coderzcolumn.com/tutorials/python/logging-config-simple-guide-to-configure-loggers-from-dictionary-and-config-files-in-python
logging_level = 'INFO'
log_config = {
    "version": 1,
    "root": {
        "handlers": ["console", "file"],
        "level": logging_level
    },
    "handlers": {
        "console": {
            "formatter": "simplefmt",
            "class": "logging.StreamHandler",
            "level": logging_level
        },
        "file": {
            "formatter": "simplefmt",
            "class": "logging.FileHandler",
            "level": logging_level,
            "filename": logging_file
        }
    },
    "formatters": {
        "simplefmt": {
            "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        }
    },
}
