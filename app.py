from flask import Flask, render_template, send_from_directory, request, url_for, redirect, jsonify, send_file
import os
import random
import base64
import io
from PIL import Image

from flask_cors import CORS, cross_origin

from settings.config import log_config, db_file, IMAGE_FOLDER
import db.db_funcs as dbf

# Logging setup
import logging
from logging import config as logging_config
logging_config.dictConfig(log_config)
logger = logging.getLogger()

app = Flask(__name__)

CORS(app)

# Initialize the database
dbf.initialize_db(db_file)
session_id = dbf.get_new_session_id(db_file)


def initialize_images_in_db():
    accepted_extensions = ['.apng', '.avif', '.gif', '.jpg', '.jpeg', '.jfif', '.pjpeg', '.pjp', '.png', '.svg', '.webp', '.bmp']
    images = os.listdir(IMAGE_FOLDER)
    images = list(set(images)) # Remove duplicates
    images = [i for i in images if os.path.splitext(i)[1].lower() in accepted_extensions]
    images.sort()  # Ensure consistent ordering
    dbf.initialize_images_session(db_file, images, session_id)
    return

@app.route('/')
def index():
    return redirect(url_for('show_image', image_id=0))

    
@app.route('/random_image64')
# @cross_origin()
def random_image64():
    filename = dbf.obtain_random_unprocessed_image(db_file, session_id)
    if filename is None or '':
        return "No unprocessed images left", 500

    image = IMAGE_FOLDER + '/' + filename
    encoded_string = get_response_scaled_image(image)
    return jsonify({"image":encoded_string , "filename":filename})

@app.route('/tag_img_get_new', methods=['POST'])
def tag_img_get_new():
    # Update the tag/classification of the image
    print('*'*50)
    content = request.get_json()
    print(content)
    classification = content['imgType']
    filename = content['filename']
    print(f"Tagging image {filename} as {classification}")
    dbf.update_image_classification(db_file, session_id, filename, classification)
    
    # Get a new image
    filename = dbf.obtain_random_unprocessed_image(db_file, session_id)
    if filename is None or '':
        return "No unprocessed images left", 500

    image = IMAGE_FOLDER + '/' + filename
    encoded_string = get_response_scaled_image(image)
    return jsonify({"image":encoded_string , "filename":filename})


def get_response_scaled_image(image_path):
    pil_img = Image.open(image_path, mode='r') # reads the PIL image
    img_format = pil_img.format

    base_width = 1000
    wpercent = (base_width / float(pil_img.size[0]))
    hsize = int((float(pil_img.size[1]) * float(wpercent)))
    pil_img = pil_img.resize((base_width, hsize), Image.Resampling.LANCZOS)


    byte_arr = io.BytesIO()
    pil_img.save(byte_arr, format=img_format) # convert the PIL image to byte array
    encoded_img = base64.encodebytes(byte_arr.getvalue()).decode('ascii') # encode as base64
    return encoded_img


if __name__ == '__main__':
    initialize_images_in_db()
    app.run(debug=True)

