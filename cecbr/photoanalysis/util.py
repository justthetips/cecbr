import json
import logging
from io import BytesIO
from typing import List

import face_recognition
import requests
from PIL import Image
from scipy.misc import imread

log = logging.getLogger(__name__)


def get_image_from_url(image_url: str, mode: str = 'RGB'):
    response = requests.get(image_url)
    img = imread(BytesIO(response.content), mode=mode)
    return img


def find_face(image_url: str, mode: str = 'RGB'):
    img = get_image_from_url(image_url, mode)
    face_locations = face_recognition.face_locations(img, 1)
    log.debug("Found {} faces".format(len(face_locations)))

    face_d = {}
    for i, face_location in enumerate(face_locations):
        face_d["Face_{}".format(i)] = face_location

    return json.dumps(face_d)


def face_landmarks(image_url: str, mode: str = 'RGB'):
    img = get_image_from_url(image_url, mode)
    landmarks = face_recognition.face_landmarks(img)
    return json.dumps(landmarks)


def face_encodings(image_url: str, mode: str = 'RGB'):
    img = get_image_from_url(image_url, mode)
    encodings = face_recognition.face_encodings(img)
    face_d = {}
    for i, face_encoding in enumerate(encodings):
        face_d["Face_{}".format(i)] = face_encoding.tolist()
    return json.dumps(face_d)


def get_faces(image_url: str, mode: str = 'RGB'):
    img = get_image_from_url(image_url, mode)
    face_locations = face_recognition.face_locations(img,1)
    log.debug("Found {} faces".format(len(face_locations)))

    faces = []
    for face_location in face_locations:
        top, right, bottom, left = face_location
        face_image = img[top:bottom, left:right]
        pil_image = Image.fromarray(face_image)
        faces.append(pil_image)
        pil_image.show()

    return faces
