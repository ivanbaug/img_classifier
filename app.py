from flask import Flask, render_template, send_from_directory, request, url_for, redirect, jsonify, send_file
import os
import random
import base64
import io
from PIL import Image

from flask_cors import CORS, cross_origin

from settings.config import log_config, db_file
import db.db_funcs as dbf

# Logging setup
import logging
from logging import config as logging_config
logging_config.dictConfig(log_config)
logger = logging.getLogger()

app = Flask(__name__)

CORS(app)

IMAGE_FOLDER = 'static/images'
DB_PATH = 'db/db.sqlite3'

images = os.listdir(IMAGE_FOLDER)
images.sort()  # Ensure consistent ordering

dbf.initialize_db(DB_PATH)

@app.route('/')
def index():
    return redirect(url_for('show_image', image_id=0))

@app.route('/image/<int:image_id>')
def show_image(image_id):
    if 0 <= image_id < len(images):
        image_name = images[(image_id)]
        next_id = (image_id + 1) % len(images)
        return render_template('index.html', image_name=image_name, next_id=next_id)
    else:
        return redirect(url_for('show_image', image_id=0))
    
@app.route('/random_image')
# @cross_origin()
def random_image():
    if len(images)>0:
        image = IMAGE_FOLDER + '/' + random.choice(images)
        return send_file(image, mimetype='image/jpeg')
    return None

    
@app.route('/random_image64')
# @cross_origin()
def random_image64():
    logger.error('Random image64')
    if len(images)>0:
        filename = random.choice(images)
        image = IMAGE_FOLDER + '/' + filename
        encoded_string = get_response_scaled_image(image)
        return jsonify({"image":encoded_string , "filename":filename})

    return None

def get_response_scaled_image(image_path):
    pil_img = Image.open(image_path, mode='r') # reads the PIL image

    base_width = 1000
    wpercent = (base_width / float(pil_img.size[0]))
    hsize = int((float(pil_img.size[1]) * float(wpercent)))
    pil_img = pil_img.resize((base_width, hsize), Image.Resampling.LANCZOS)


    byte_arr = io.BytesIO()
    pil_img.save(byte_arr, format='JPEG') # convert the PIL image to byte array
    encoded_img = base64.encodebytes(byte_arr.getvalue()).decode('ascii') # encode as base64
    return encoded_img

if __name__ == '__main__':
    app.run(debug=True)

