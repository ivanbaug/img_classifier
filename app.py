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
# session_id = dbf.get_new_session_id(db_file)


def initialize_images_in_db():
    accepted_extensions = ['.apng', '.avif', '.gif', '.jpg', '.jpeg', '.jfif', '.pjpeg', '.pjp', '.png', '.svg', '.webp', '.bmp']
    images = os.listdir(IMAGE_FOLDER)
    images = [i for i in images if os.path.splitext(i)[1].lower() in accepted_extensions] # Filter out non-image files
    images_set = set(images)

    images = list(images_set) # Remove duplicates


    # Set values not available
    dbf.set_not_available(db_file)

    # Get list of sessions
    sessions = dbf.get_sessions(db_file)

    for session in sessions:
        simgs = dbf.get_imgs_from_session(db_file, session['session_id'])
        simgs_set = set(simgs)

        qty_imgs = len(images_set)
        qty_session_imgs = len(simgs_set)

        if qty_imgs == qty_session_imgs:
            if images_set == simgs_set:
                # All images in folder are already in the database.
                session['imgs_are_available'] = True
                dbf.set_session_imgs_available(db_file, session['session_id'])
                continue

        qty_diff = qty_session_imgs - qty_imgs
        if qty_diff > 0:
            diff_imgs = simgs_set.difference(images_set)
            if qty_diff != len(diff_imgs):
                # All images in the database are not in the folder
                continue
            # There are more images in folder but the old ones are still there, so it's safe to add the new ones 
            dbf.initialize_images_session(db_file, list(diff_imgs),session['session_id'])
            session['imgs_are_available'] = True
            dbf.set_session_imgs_available(db_file, session['session_id'])
            continue
        else:
            # Some images in the database are not in the folder
            continue
    
    if any([session['imgs_are_available'] for session in sessions]):
        # At least one session exists with all images available
        return

    new_session_id = dbf.new_session(db_file, len(images), 0, True)
    dbf.initialize_images_session(db_file, images, new_session_id)
    return

@app.route('/')
def index():
    return redirect(url_for('show_image', image_id=0))

    
@app.route('/random_image64')
# @cross_origin()
def random_image64():
    print(request.args)
    session_id = request.args.get('session')
    if not session_id:
        return jsonify({"success":False, "info": "No session ID received"})

    filename = dbf.obtain_random_unprocessed_image(db_file, session_id)
    if not filename:
        return jsonify({"success":False, "info": "No unprocessed images left"})

    image = IMAGE_FOLDER + '/' + filename
    encoded_string = get_response_scaled_image(image)
    return jsonify({"success":True, "image":encoded_string , "filename":filename, "info": "OK"})

@app.route('/tag_img_get_new', methods=['POST'])
def tag_img_get_new():
    # Update the tag/classification of the image
    # print('*'*50)
    content = request.get_json()
    # print(content)
    classification = content['imgType']
    filename = content['filename']
    session_id = content['sessionId']
    print(f"Tagging image {filename} as {classification}")
    dbf.update_image_classification(db_file, session_id, filename, classification)
    dbf.update_session_processed_count(db_file, session_id)
    
    # Get a new image
    filename = dbf.obtain_random_unprocessed_image(db_file, session_id)

    if not filename:
        return jsonify({"success":False, "info": "No unprocessed images left"})

    # if filename is None or '':
    #     return "No unprocessed images left", 500

    image = IMAGE_FOLDER + '/' + filename
    encoded_string = get_response_scaled_image(image)
    return jsonify({"success":True, "image":encoded_string , "filename":filename, "info": "OK"})


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


@app.route('/get_available_sessions')
# @cross_origin()
def get_available_sessions():
    sessions = dbf.get_sessions(db_file, imgs_are_available=True)
    return jsonify({"success":True, "data":sessions, "info": "OK"})

if __name__ == '__main__':
    initialize_images_in_db()
    app.run(debug=True)

# set([1,2,3,4]).difference(setb)