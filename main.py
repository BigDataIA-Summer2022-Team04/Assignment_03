import os
import logging
import models
import pandas as pd
from database import engine, SessionLocal
from routers import predict, users, authentication
from google.cloud import bigquery
from fastapi import FastAPI, Depends, status, HTTPException
from custom_functions import logfunc
from fastapi.staticfiles import StaticFiles
import json
import schemas
from routers.oaut2 import get_current_user
from fastapi import FastAPI,status,HTTPException

#################################################
# Author: Piyush
# Creation Date: 13-July-22
# Last Modified Date:
# Change Logs:
# SL No         Date            Changes
# 1             13-July-22      First Version
# 
#################################################


# load_dotenv()
# DONE: Change path before deployment
os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = '/keys/key.json'
# LOGLEVEL = os.environ.get('LOGLEVEL', 'INFO').upper()
logging.basicConfig(
    format='%(asctime)s %(levelname)-8s %(message)s',
    level="DEBUG", # INFO DEBUG ERROR
    datefmt='%Y-%m-%d %H:%M:%S')



app = FastAPI(title="Image Classification")

models.Base.metadata.create_all(bind=engine)


# app.include_router(plot.router)
app.include_router(predict.router)
app.include_router(users.router)
app.include_router(authentication.router)
app.mount("/", StaticFiles(directory="ui", html=True), name="ui")




def exit_script(error_code: int):
    logging.info(f"Script Ends")
    exit(error_code)


def big_query_handshake(sample_query: str = r"SELECT YEAR_MFR FROM `plane-detection-352701.SPY_PLANE.FAA` LIMIT 5"):
    logging.info(f"Handshake | Connecting to Big-Query")
    if not os.path.isfile(os.getenv('BQ_KEY_JSON')):
        logging.error(f"User input file not found, Re-Verify the path {os.getenv('BQ_KEY_JSON')}")
        return 105
    try:
        client = bigquery.Client()
        logging.info(f"Handshake | Connection established to Big-Query")
    except Exception as e:
        logging.error(f"Handshake | Cannot establish Handshake with Big-Query. \nException: {e}")
        return 101
    logging.info(f"Handshake | Fetching data from Big-Query")
    try:
        df = client.query(sample_query).to_dataframe()
    except Exception as e:
        logging.error(f"Handshake | Bad SQL Query, Please Re-Verify SQL \nException: {e}")
        return 104
    if df.empty:
        logging.error(f"No rows returned from big query")
        return 103
    return 0


if __name__ == "__main__":
    handshake_return_code = big_query_handshake()
    if handshake_return_code in (101,102,103,104,105):
        logging.info(f"Handshake | Failed, Existing Script")
        exit_script(handshake_return_code)
    else:
        logging.info(f"Handshake | Success, Launching API Server")
        # uvicorn.run(app, host="127.0.0.1", port=9000)
