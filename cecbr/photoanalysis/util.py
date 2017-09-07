from PIL import Image
import face_recognition
from scipy.misc import imread
import requests
from io import BytesIO


import logging
import json

log = logging.getLogger(__name__)

def get_image_from_url(image_url:str,mode:str='RGB'):
    response = requests.get(image_url)
    img =imread(BytesIO(response.content),mode=mode)
    return img


def find_face(image_url:str,mode:str='RGB'):
    img = get_image_from_url(image_url,mode)
    face_locations = face_recognition.face_locations(img,1)
    log.debug("Found {} faces".format(len(face_locations)))

    face_d = {}
    for i, face_location in enumerate(face_locations):
        face_d["Face_{}".format(i)] = face_location

    return json.dumps(face_d)


def face_landmarks(image_url:str,mode:str='RGB'):
    img = get_image_from_url(image_url,mode)
    landmarks = face_recognition.face_landmarks(img)
    return json.dumps(landmarks)


def face_encodings(image_url:str,mode:str='RGB'):
    img = get_image_from_url(image_url, mode)
    encodings = face_recognition.face_encodings(img)
    face_d = {}
    for i, face_encoding in enumerate(encodings):
        face_d["Face_{}".format(i)] = face_encoding.tolist()
    return json.dumps(face_d)

