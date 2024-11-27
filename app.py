from flask import Flask, render_template, send_from_directory, request, url_for, redirect, jsonify, send_file
import os
import random
import base64
import io
from PIL import Image

import shutil

from flask_cors import CORS, cross_origin

from settings.config import log_config, db_file, INPUT_IMAGE_FOLDER, SESSION_OUTPUT_FOLDER
import db.db_funcs as dbf
import classifier.classifier as clf

# Logging setup
import logging
from logging import config as logging_config
logging_config.dictConfig(log_config)
logger = logging.getLogger()

app = Flask(__name__, static_folder='./frontend/dist', static_url_path='')

CORS(app)

# Initialize the database
dbf.initialize_db(db_file)
# session_id = dbf.get_new_session_id(db_file)


def initialize_images_in_db():
    accepted_extensions = ['.apng', '.avif', '.gif', '.jpg', '.jpeg', '.jfif', '.pjpeg', '.pjp', '.png', '.svg', '.webp', '.bmp']
    images = os.listdir(INPUT_IMAGE_FOLDER)
    images = [i for i in images if os.path.splitext(i)[1].lower() in accepted_extensions] # Filter out non-image files
    images_set = set(images)

    images = list(images_set) # Remove duplicates

    # Set values not available
    dbf.set_not_available(db_file)

    # Get list of sessions
    sessions = dbf.get_sessions(db_file)

    for session in sessions:
        dbf.update_session_labeled_count(db_file, session['session_id'])
        simgs = dbf.get_img_names_from_session(db_file, session['session_id'])
        simgs_set = set(simgs)

        qty_imgs = len(images_set)
        qty_session_imgs = len(simgs_set)

        if qty_imgs == qty_session_imgs:
            if images_set == simgs_set:
                # All images in folder are already in the database.
                session['imgs_are_available'] = True
                dbf.set_session_imgs_available(db_file, session['session_id'])
                continue

        qty_diff = qty_imgs - qty_session_imgs
        if qty_diff > 0:
            # There are more images in the folder than in the session in db
            diff_imgs = images_set.difference(simgs_set)

            if qty_diff != len(diff_imgs):
                # All images in the database are not in the folder
                continue
            # There are more images in folder but the old ones are still there, so it's safe to add the new ones 
            dbf.initialize_images_session(db_file, list(diff_imgs),session['session_id'])
            session['imgs_are_available'] = True
            dbf.set_session_imgs_available(db_file, session['session_id'])
            dbf.update_session_labeled_count(db_file, session['session_id'])
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
    initialize_images_in_db()
    return send_from_directory(app.static_folder, 'index.html')

@app.route('/classify')
def classify():
    session_id = request.args.get('session')
    return send_from_directory(app.static_folder, 'classify/index.html')
    
@app.route('/api/random_image64')
# @cross_origin()
def random_image64():
    print(request.args)
    session_id = request.args.get('session')
    if not session_id:
        return jsonify({"success":False, "info": "No session ID received"})

    filename, predicted_label = dbf.get_unprocessed_prediction(db_file, session_id)
    list_not_empty = True # Assumes there are images to predict
    stats = dbf.get_stats_from_session(db_file, session_id)
    if not filename:
        list_not_empty = clf.predict_images(session_id=session_id, image_amount=50)
        filename, predicted_label = dbf.get_unprocessed_prediction(db_file, session_id)

    if not list_not_empty and not filename:
        # No predicted images
        filename = dbf.obtain_random_unlabeled_image(db_file, session_id)
        if not filename:
            return jsonify({"success":False, "info": "No unlabeled images left", "stats":stats})

    image = INPUT_IMAGE_FOLDER + '/' + filename
    encoded_string = get_response_scaled_image(image)

    

    return jsonify({"success":True, "image":encoded_string , "filename":filename, "info": "OK", "stats":stats, "predicted": predicted_label})

@app.route('/api/tag_img_get_new', methods=['POST'])
def tag_img_get_new():
    # Update the tag/label of the image
    content = request.get_json()
    label = content['imgType']
    filename = content['filename']
    session_id = content['sessionId']
    print(f"Tagging image {filename} as {label}")
    dbf.update_image_label(db_file, session_id, filename, label)
    dbf.set_prediction_processed(db_file,filename, session_id)
    labeled_count, total_count = dbf.update_session_labeled_count(db_file, session_id)
    
    # Get a new image
    # filename = dbf.obtain_random_unlabeled_image(db_file, session_id)
    filename, predicted_label = dbf.get_unprocessed_prediction(db_file, session_id)
    list_not_empty = True # Assumes there are images to predict
    stats = dbf.get_stats_from_session(db_file, session_id)
    if not filename:
        list_not_empty = clf.predict_images(session_id=session_id, image_amount=50)
        filename, predicted_label = dbf.get_unprocessed_prediction(db_file, session_id)

    if not list_not_empty and not filename:
        # No predicted images
        filename = dbf.obtain_random_unlabeled_image(db_file, session_id)
        if not filename:
            return jsonify({"success":False, "info": "No unlabeled images left", "stats":stats})

    image = INPUT_IMAGE_FOLDER + '/' + filename
    encoded_string = get_response_scaled_image(image)

    
    return jsonify({"success":True, "image":encoded_string , "filename":filename, "info": "OK", "stats":stats, "predicted": predicted_label})


def get_response_scaled_image(image_path):
    pil_img = Image.open(image_path, mode='r') # reads the PIL image
    img_format = pil_img.format

    base_width = 1000
    wpercent = (base_width / float(pil_img.size[0]))
    hsize = int((float(pil_img.size[1]) * float(wpercent)))
    pil_img = pil_img.resize((base_width, hsize), Image.Resampling.LANCZOS)


    byte_arr = io.BytesIO()
    # pil_img.save(byte_arr, format=img_format) # convert the PIL image to byte array
    pil_img.save(byte_arr, format=img_format) # convert the PIL image to byte array

    encoded_img = base64.encodebytes(byte_arr.getvalue()).decode('ascii') # encode as base64
    return encoded_img


@app.route('/api/copy_imgs_to_new_folder')
# @cross_origin()
def copy_imgs_to_new_folder():
    print(request.args)
    session_id = request.args.get('session')
    if not session_id:
        return jsonify({"success":False, "info": "No session ID received"})
    
    imgs_list = dbf.get_imgs_from_session(db_file, session_id)

    img_classes = dbf.get_image_classes(db_file, session_id)

    # Check if output folder exists
    if not os.path.exists(SESSION_OUTPUT_FOLDER):
        os.makedirs(SESSION_OUTPUT_FOLDER)

    # Create subfolder with session id and create it if it doesn't exist
    output_folder = SESSION_OUTPUT_FOLDER + '/S' + session_id
    if not os.path.exists(output_folder):
        os.makedirs(output_folder)

    # Create subfolders for each class
    for img_class in img_classes:
        if not os.path.exists(output_folder + '/' + img_class):
            os.makedirs(output_folder + '/' + img_class)

    for image in imgs_list:
        if image['label']:
            # check if metadata file exists in input folder
            if os.path.exists(INPUT_IMAGE_FOLDER + '/' + image['name'] + '.json'):
                shutil.copy(INPUT_IMAGE_FOLDER + '/' + image['name'] + '.json', output_folder + '/' +  image['label'] + '/' + image['name'] + '.json')

            shutil.copy(INPUT_IMAGE_FOLDER + '/' + image['name'], output_folder + '/' +  image['label'] + '/' + image['name'])

    return jsonify({"success":True,  "info": "Done :)"})

@app.route('/api/get_available_sessions')
# @cross_origin()
def get_available_sessions():
    sessions = dbf.get_sessions(db_file, imgs_are_available=True)
    return jsonify({"success":True, "data":sessions, "info": "OK"})


@app.route('/api/train_model', methods=['POST'])
def train_model():
    # session_id = request.args.get('sessionId')
    # full_train = request.args.get('fullTrain')
    content = request.get_json()
    session_id = content['sessionId']
    full_train = content['fullTrain']
    if not session_id:
        return jsonify({"success":False, "info": "No session ID received"})

    try:
        clf.train_model_by_session(db_file, session_id, full_train=full_train)
    except ValueError as e:
        return jsonify({"success":False, "info": str(e)})
    return jsonify({"success":True, "info": "OK"})



if __name__ == '__main__':
    initialize_images_in_db()
    app.run(debug=True)
