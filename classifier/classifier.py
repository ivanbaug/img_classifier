import tensorflow as tf
import numpy as np
import os
import matplotlib.pyplot as plt
import matplotlib.image as mpimg
from settings.config import log_config, db_file, INPUT_IMAGE_FOLDER, CLS_MODEL_FOLDER
import db.db_funcs as dbf

import logging
from logging import config as logging_config
from tensorflow.python.framework.errors_impl import InvalidArgumentError
logging_config.dictConfig(log_config)
logger = logging.getLogger()

batch_size = 32

def get_or_create_model(session_id: int, number_of_classes: int) -> tf.keras.models.Sequential:
    """
    Get the model from the file system or create a new one.
    """
    model_file = CLS_MODEL_FOLDER + f'/model_{session_id}.h5'
    if os.path.exists(model_file):
        model = tf.keras.models.load_model(model_file)
    else:
        model = model = tf.keras.models.Sequential([
            # Note the input shape is the desired size (batch[0].shape) of the image 256x256 with 3 bytes color
            # This is the first convolution
            tf.keras.layers.Conv2D(64, (3,3), activation='relu', input_shape=(256, 256, 3)),
            tf.keras.layers.MaxPooling2D(2, 2),
            # The second convolution
            tf.keras.layers.Conv2D(128, (3,3), activation='relu'),
            tf.keras.layers.MaxPooling2D(2,2),
            # The third convolution
            tf.keras.layers.Conv2D(64, (3,3), activation='relu'),
            tf.keras.layers.MaxPooling2D(2,2),
            # Flatten the results to feed into a DNN
            tf.keras.layers.Flatten(),
            tf.keras.layers.Dropout(0.5),
            # 512 neuron hidden layer
            tf.keras.layers.Dense(512, activation='relu'),
            tf.keras.layers.Dense(number_of_classes, activation='softmax')
        ])
        model.compile(loss = 'categorical_crossentropy', optimizer='rmsprop', metrics=['accuracy'])
    # TODO: Create a pretrained model to initialize if desired
    return model

def save_model(model: tf.keras.models.Sequential, session_id: int):
    """
    Save the model to the file system.
    """
    model_file = CLS_MODEL_FOLDER + f'/model_{session_id}.h5'
    model.save(model_file, overwrite=True)


def fine_tune_model(model: tf.keras.models.Sequential, train, val, epochs=25):
    """
    Fine tune the model with the given data.
    """
    history = model.fit(train, epochs=epochs, validation_data = val, verbose = 1)
    return model, history


def extract_labels_and_mappings(data_list: list[dict]) -> tuple[list[str], int, dict[str, int], dict[int, str], dict[str, np.ndarray]]:
    """
    Extract the labels and mappings from the data list.
    """
    class_names = sorted(set(item["class"] for item in data_list))
    number_of_classes = len(class_names)
    map_label_to_index = {label: index for index, label in enumerate(class_names)}
    map_index_to_label = {index: label for label, index in map_label_to_index.items()}
    map_label_to_categorical = {label: tf.keras.utils.to_categorical(index, num_classes=len(class_names)) for index, label in map_index_to_label.items()}
    return class_names, number_of_classes, map_label_to_index, map_index_to_label, map_label_to_categorical

def load_image(filename, label):
    """
    Load and preprocess each image.
    """
    image = tf.io.read_file(filename)
    image = tf.image.decode_image(image, channels=3, expand_animations = False)
    image = tf.image.resize(image, [256, 256])
    return image, label

def create_dataset(data_list: list[dict]) -> tf.data.Dataset:   
    """
    Create a dataset from the data list.
    """
    filenames = [item['filename'] for item in data_list]
    # print(filenames)
    labels = [item['label'] for item in data_list]
    
    # Create a dataset from the filenames and labels
    dataset = tf.data.Dataset.from_tensor_slices((filenames, labels))
    
    # Map the process_image function to each element
    dataset = dataset.map(load_image)
    
    return dataset

def train_model_by_session(db_file, session_id, full_train=False):
    """
    Train the model with the given session id.
    """

    # Full train or fine tune
    if full_train:
        data_list = dbf.get_all_labeled_images(db_file, session_id)
    else:
        data_list = dbf.get_unprocessed_labeled_images(db_file, session_id)

    if (len(data_list) < batch_size+1):
        logger.error(f"Too few images to train: {len(data_list)}")
        raise ValueError("Too few labeled images to train")

    
    class_names, number_of_classes, map_label_to_index, map_index_to_label, map_label_to_categorical = extract_labels_and_mappings(data_list)

    dbf.save_label_map(db_file, session_id, map_index_to_label)
    
    for item in data_list:
        item["label"] = map_label_to_categorical[item["class"]]

    dataset = create_dataset(data_list)

    ## Batch the dataset
    dataset = dataset.batch(batch_size)

    data_iterator = dataset.as_numpy_iterator()
    # Scale data
    dataset = dataset.map(lambda x, y: (x / 255.0, y))
    scaled_iterator = dataset.as_numpy_iterator()

    # Split data
    # test_size = int(0.1 * len(dataset)) or 1
    # val_size = int(0.2 * len(dataset)) or 1
    val_size = int(0.2 * len(dataset)) or 1
    # train_size = len(dataset) - test_size - val_size
    train_size = len(dataset) - val_size
    logger.info(f"train_size: {train_size} val_size: {val_size}")

    train = dataset.take(train_size)
    val = dataset.skip(train_size).take(val_size)
    # test = dataset.skip(train_size + val_size).take(test_size)

    steps_per_epoch = len(train)//train_size
    validation_steps = len(val)//val_size

    logger.info(f"steps_per_epoch: {steps_per_epoch}")
    logger.info(f"validation_steps: {validation_steps}")

    model = get_or_create_model(session_id, number_of_classes)

    if full_train:
        model, history = fine_tune_model(model, train, val)
    else:
        model, history = fine_tune_model(model, train, val, epochs=5)

    save_model(model, session_id)

    # Finally set images in the session as processed
    dbf.set_images_processed(db_file, session_id)    


def predict_image(image_path, session_id):
    """
    Predict the image with the given session id.
    """
    model = tf.keras.models.load_model(CLS_MODEL_FOLDER + f'/model_{session_id}.h5')
    image = tf.io.read_file(image_path)
    image = tf.image.decode_image(image, channels=3, expand_animations = False)
    image = tf.image.resize(image, [256, 256])
    image = tf.expand_dims(image, axis=0)
    image = image / 255.0
    prediction = model.predict(image)

    #get labels and mappings
    map_index_to_label = dbf.get_label_map(db_file, session_id) # try to get the label map from the database
    if not map_index_to_label:
        data_list = dbf.get_all_labeled_images(db_file, session_id)
        class_names, number_of_classes, map_label_to_index, map_index_to_label, map_label_to_categorical = extract_labels_and_mappings(data_list)


    return map_index_to_label[np.argmax(prediction)]

def predict_images(session_id, image_amount) -> bool:
    """
    Predict the images with the given session id.
    Return True if there are images to predict, False otherwise.
    """

    image_list = dbf.obtain_unlabeled_images_from_session(db_file, session_id)
    if not image_list:
        return False


    map_index_to_label = dbf.get_label_map(db_file, session_id) # try to get the label map from the database
    if not map_index_to_label:
        data_list = dbf.get_all_labeled_images(db_file, session_id)
        class_names, number_of_classes, map_label_to_index, map_index_to_label, map_label_to_categorical = extract_labels_and_mappings(data_list)

    model_filepath = CLS_MODEL_FOLDER + f'/model_{session_id}.h5'
    if not os.path.exists(model_filepath):
        map_index_to_label = dbf.get_label_map(db_file, 2) # try to get the label map from the database
        model_filepath = CLS_MODEL_FOLDER + f'/model_base.h5'
        if not os.path.exists(model_filepath):
            logger.error(f"Model file not found: {model_filepath}")
            return None

    model = tf.keras.models.load_model(model_filepath)
    for image_name in image_list[:image_amount]:
        image_path = INPUT_IMAGE_FOLDER + '/' + image_name
        image = tf.io.read_file(image_path)
        try:
            image = tf.image.decode_image(image, channels=3, expand_animations = False)
            image = tf.image.resize(image, [256, 256])
            image = tf.expand_dims(image, axis=0)
            image = image / 255.0
            prediction = model.predict(image)
            dbf.add_prediction(db_file, image_name, map_index_to_label[np.argmax(prediction)], session_id)
        except InvalidArgumentError as e:
            import traceback
            tb = traceback.format_exc()
            dbf.new_exc_error(db_file, session_id, tb, image_path)
            logger.error(f"{tb}")
            logger.error(f"Error predicting image: {image_path}")
    
    return True