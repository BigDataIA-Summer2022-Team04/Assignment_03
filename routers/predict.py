
import logging
from typing import Union
from google.cloud import bigquery
from custom_functions import logfunc
from fastapi import APIRouter, HTTPException, Response, status, Query, Depends
import schemas
from routers.oaut2 import get_current_user
from fastapi import FastAPI, File, UploadFile
import numpy as np
from io import BytesIO
from PIL import Image
import tensorflow as tf
import math 
import os
router = APIRouter(
    prefix="/maas",
    tags=['Prediction']
)

model_cutmix = tf.keras.models.load_model("models/cutmix/cutmix.h5")
model_mixup = tf.keras.models.load_model("models/mixup")
model_augmix = tf.keras.models.load_model("models/augmix")
class_name = ["Defective", "Not Defective"]


@router.post('/predict', status_code=status.HTTP_200_OK)
async def get_registrant( model_name: str, file: UploadFile = File(...),
                        get_current_user: schemas.ServiceAccount = Depends(get_current_user)
                        ):
    if model_name.lower() not in ['cutmix', 'mixup', 'augmix']:
        logfunc(get_current_user.email, "/daas/predict" + model_name.lower(), 400)
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,detail="Please select one model between cutmix, mixup, augmix" )
    contents = await file.read()

    if model_name == "cutmix":
        try:
            with open("image.jpeg", 'wb') as img_file:
                img_file.write(contents)
            image = np.array(tf.keras.utils.load_img("image.jpeg",target_size=(300, 300),color_mode='rgb'))
            os.remove("image.jpeg")
            image = image.astype("float32") / 255.0
            img_batch = np.reshape(image, (-1, 300, 300, 3))
            predictions = model_cutmix.predict(img_batch)
        except Exception as e:
            logging.error(f"Error reading image \n {e}")
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,detail="Please upload a valid image")
        
    elif model_name == "mixup":
        try:
            with open("image.jpeg", 'wb') as img_file:
                img_file.write(contents)
            image = np.array(tf.keras.utils.load_img("image.jpeg",target_size=(28, 28),color_mode='grayscale'))
            os.remove("image.jpeg")
            image = image.astype("float32") / 255.0
            img_batch = np.reshape(image, (-1, 28, 28, 1))
            predictions = model_mixup.predict(img_batch)
        except Exception as e:
            logging.error(f"Error reading image \n {e}")
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,detail="Please upload a valid image")
    elif model_name == "augmix":
        try:
            with open("image.jpeg", 'wb') as img_file:
                img_file.write(contents)
            image = np.array(tf.keras.utils.load_img("image.jpeg",target_size=(28, 28),color_mode='rgb'))
            os.remove("image.jpeg")
            image = image.astype("float32") / 255.0
            img_batch = np.reshape(image, (-1, 28, 28, 3))
            predictions = model_augmix.predict(img_batch)
        except Exception as e:
            logging.error(f"Error reading image \n {e}")
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,detail="Please upload a valid image")
    
    predicted_class = class_name[np.argmax(predictions)]
    confidence = np.max(predictions)
    logfunc(get_current_user.email, "/daas/predict/" + model_name.lower(), 200)
    return {
        'prediction': predicted_class,
        'confidence': "0.00" if math.isnan(confidence) else "{:.2f}".format(float(confidence)*100)
    }
    