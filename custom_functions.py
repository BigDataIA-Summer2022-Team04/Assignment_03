from google.cloud import bigquery
import logging

#################################################
# Author: Piyush
# Creation Date: 17-Jun-22
# Last Modified Date:
# Change Logs:
# SL No         Date            Changes
# 1             17-Jun-22       First Version
# 2             24-Jun-22       Log Function
# 3             13-Jul-22       Remove state function
#################################################


def logfunc(username: str, endpoint:str, response_code: int):
    logging.info(f"Writing logs to bigQuery")
    client = bigquery.Client()
    query_string = f"""
    INSERT INTO `plane-detection-352701.SPY_PLANE.logs` VALUES (
    CAST(CURRENT_TIMESTAMP() AS STRING ), '{username}', '{endpoint}', {response_code}, (SELECT MAX(logid)+1 AS ID from `plane-detection-352701.SPY_PLANE.logs`))
    """
    # logging.info(f"query_string : {query_string}")
    try:
        df = client.query(query_string)
        print(df)
    except Exception as e:
        logging.error(f"Exception: {e}")
        logging.error(f"Error Writing logs to BigQuery")
        return
    logging.info(f"Writing logs to bigQuery Completed")
