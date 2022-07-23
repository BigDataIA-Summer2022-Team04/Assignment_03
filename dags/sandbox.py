import json
import os 
import requests
import glob
import io
import time
import numpy as np
import pandas as pd
import tensorflow as tf
from PIL import Image
import urllib.request
import shutil
from airflow.models import DAG
import os
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail
from airflow.utils.dates import days_ago
from airflow.operators.python_operator import PythonOperator
from airflow.operators.bash_operator import BashOperator
from google.cloud import storage

os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = "/opt/airflow/keys/key.json"

args = {
 
    'owner': 'Anku',
    'start_date': days_ago(0),
    'email': ['anand.pi@northeastern.edu'],
	'email_on_failure': True
}
 
dag = DAG(dag_id = 'Prediction_comparision_v1',
            default_args=args,
            schedule_interval="0 * * * *")
 
 
def authenticate_to_API(ti):
    print('Get Token')
    url = "https://maasapi.anandpiyush.com/login"
    payload={'username': "anand.pi@northeastern.edu", 'password': "****************"}
    response = requests.request("POST", url, data=payload)
    # print(response.status_code)
    json_data = json.loads(response.text)
    # print(json_data["access_token"])
    # return json_data["access_token"]
    ti.xcom_push(key='access_token', value=json_data["access_token"])
 
def process_mixup(ti):
    auth_token = ti.xcom_pull(task_ids='authenticate_to_API', key='access_token')
    ts = time.strftime("%Y-%m-%d_%H:%M:%S")
    labels_pred = []
    labels_test = []
    failure_list = []

    def_front = glob.glob('/opt/airflow/working_data/test/test/def_front/*.*')
    ok_front = glob.glob('/opt/airflow/working_data/test/test/ok_front/*.*')

    total_file_count = len(def_front) + len(ok_front)
    ti.xcom_push(key='total_file_count', value=total_file_count)

    for i in def_front:
        im = Image.open(i)
        im_resize = im.resize((300, 300))
        buf = io.BytesIO()
        im_resize.save(buf, format='JPEG')
        bytes_data = buf.getvalue()

        url = f"https://maasapi.anandpiyush.com/maas/predict?model_name=mixup"
        headers = {}
        files={'file': bytes_data}
        headers['Authorization'] = f"Bearer {auth_token}"
        response = requests.request("POST", url, headers=headers, files=files)
        # print(response.status_code)
        if response.status_code == 200:
            json_data = json.loads(response.text)
            prediction = json_data["prediction"]
            if prediction == "Defective":
                labels_pred.append(1)
            else:
                labels_pred.append(0)
            labels_test.append(1)
        else:
            print(f"File_name: {i.split('/')[-1]} Return Code: {response.status_code} Text : {response.text}")
            failure_list.append(i.split('/')[-1])
            continue

    for i in ok_front:
        im = Image.open(i)
        im_resize = im.resize((300, 300))
        buf = io.BytesIO()
        im_resize.save(buf, format='JPEG')
        bytes_data = buf.getvalue()

        url = f"https://maasapi.anandpiyush.com/maas/predict?model_name=mixup"
        headers = {}
        files={'file': bytes_data}
        headers['Authorization'] = f"Bearer {auth_token}"
        response = requests.request("POST", url, headers=headers, files=files)
        if response.status_code == 200:
            # print(response.status_code)
            json_data = json.loads(response.text)
            prediction = json_data["prediction"]
            if prediction == "Defective":
                labels_pred.append(1)
            else:
                labels_pred.append(0)
            labels_test.append(0)
        else:
            print(f"File_name: {i.split('/')[-1]} Return Code: {response.status_code} Text : {response.text}")
            failure_list.append(i.split('/')[-1])
            continue
    ti.xcom_push(key='mixup_failure_list', value=' '.join(failure_list))
    ti.xcom_push(key='mixup_process_count', value=len(labels_pred))
    labels_pred = np.array(labels_pred, dtype=np.uint8)
    labels_test = np.array(labels_test, dtype=np.uint8)
    cm = tf.math.confusion_matrix(labels_test, labels_pred )

    print("Confusion")
    print(cm)
    print(f"labels_test : {len(labels_test)}")
    print(f"labels_pred : {len(labels_pred)}")
    
    file_name = f"/opt/airflow/working_data/{ts}-UTC_mixup"
    # file = open(file_name, "w+")
    # # Saving the array in a text file
    # content = str(cm)
    # file.write(content)
    # file.close()
    np.save(file_name, cm.numpy())

    file_name = file_name + ".npy"

    report_url =  upload_blob("airflow-run-cm", file_name, file_name.split('/')[-1])
    ti.xcom_push(key='mixup_file_report', value=report_url)

def process_cutmix(ti):
    auth_token = ti.xcom_pull(task_ids='authenticate_to_API', key='access_token')
    ts = time.strftime("%Y-%m-%d_%H:%M:%S")
    labels_pred = []
    labels_test = []
    failure_list = []

    def_front = glob.glob('/opt/airflow/working_data/test/test/def_front/*.*')
    ok_front = glob.glob('/opt/airflow/working_data/test/test/ok_front/*.*')


    for i in def_front:
        im = Image.open(i)
        im_resize = im.resize((300, 300))
        buf = io.BytesIO()
        im_resize.save(buf, format='JPEG')
        bytes_data = buf.getvalue()

        url = f"https://maasapi.anandpiyush.com/maas/predict?model_name=cutmix"
        headers = {}
        files={'file': bytes_data}
        headers['Authorization'] = f"Bearer {auth_token}"
        response = requests.request("POST", url, headers=headers, files=files)
        if response.status_code == 200:
            # print(response.status_code)
            # print(response.text)
            json_data = json.loads(response.text)
            prediction = json_data["prediction"]
            if prediction == "Defective":
                labels_pred.append(1)
            else:
                labels_pred.append(0)
            labels_test.append(1)
        else:
            print(f"File_name: {i.split('/')[-1]} Return Code: {response.status_code} Text : {response.text}")
            failure_list.append(i.split('/')[-1])
            continue

    for i in ok_front:
        im = Image.open(i)
        im_resize = im.resize((300, 300))
        buf = io.BytesIO()
        im_resize.save(buf, format='JPEG')
        bytes_data = buf.getvalue()

        url = f"https://maasapi.anandpiyush.com/maas/predict?model_name=cutmix"
        headers = {}
        files={'file': bytes_data}
        headers['Authorization'] = f"Bearer {auth_token}"
        response = requests.request("POST", url, headers=headers, files=files)
        if response.status_code == 200:
            # print(response.status_code)
            # print(response.text)
            json_data = json.loads(response.text)
            prediction = json_data["prediction"]
            if prediction == "Defective":
                labels_pred.append(1)
            else:
                labels_pred.append(0)
            labels_test.append(0)
        else:
            print(f"File_name: {i.split('/')[-1]} Return Code: {response.status_code} Text : {response.text}")
            failure_list.append(i.split('/')[-1])
            continue
    ti.xcom_push(key='cutmix_failure_list', value=' '.join(failure_list))
    ti.xcom_push(key='cutmix_process_count', value=len(labels_pred))
    labels_pred = np.array(labels_pred, dtype=np.uint8)
    labels_test = np.array(labels_test, dtype=np.uint8)
    cm = tf.math.confusion_matrix(labels_test, labels_pred )

    print("Confusion")
    print(cm)
    print(f"labels_test : {len(labels_test)}")
    print(f"labels_pred : {len(labels_pred)}")
    
    file_name = f"/opt/airflow/working_data/{ts}-UTC_cutmix"
    np.save(file_name, cm.numpy())
    file_name = file_name + ".npy"
    # return upload_blob("airflow-run-cm", file_name, file_name.split('/')[-1])
    report_url =  upload_blob("airflow-run-cm", file_name, file_name.split('/')[-1])
    ti.xcom_push(key='cutmix_file_report', value=report_url)

def process_augmix(ti):
    auth_token = ti.xcom_pull(task_ids='authenticate_to_API', key='access_token')
    ts = time.strftime("%Y-%m-%d_%H:%M:%S")
    labels_pred = []
    labels_test = []
    failure_list = []

    def_front = glob.glob('/opt/airflow/working_data/test/test/def_front/*.*')
    ok_front = glob.glob('/opt/airflow/working_data/test/test/ok_front/*.*')

    for i in def_front:
        im = Image.open(i)
        im_resize = im.resize((300, 300))
        buf = io.BytesIO()
        im_resize.save(buf, format='JPEG')
        bytes_data = buf.getvalue()

        url = f"https://maasapi.anandpiyush.com/maas/predict?model_name=augmix"
        headers = {}
        files={'file': bytes_data}
        headers['Authorization'] = f"Bearer {auth_token}"
        response = requests.request("POST", url, headers=headers, files=files)
        if response.status_code == 200:
            # print(response.status_code)
            # print(response.text)
            json_data = json.loads(response.text)
            prediction = json_data["prediction"]
            if prediction == "Defective":
                labels_pred.append(1)
            else:
                labels_pred.append(0)
            labels_test.append(1)
        else:
            print(f"File_name: {i.split('/')[-1]} Return Code: {response.status_code} Text : {response.text}")
            failure_list.append(i.split('/')[-1])
            continue

    for i in ok_front:
        im = Image.open(i)
        im_resize = im.resize((300, 300))
        buf = io.BytesIO()
        im_resize.save(buf, format='JPEG')
        bytes_data = buf.getvalue()

        url = f"https://maasapi.anandpiyush.com/maas/predict?model_name=augmix"
        headers = {}
        files={'file': bytes_data}
        headers['Authorization'] = f"Bearer {auth_token}"
        response = requests.request("POST", url, headers=headers, files=files)
        if response.status_code == 200:
            # print(response.status_code)
            # print(response.text)
            json_data = json.loads(response.text)
            prediction = json_data["prediction"]
            if prediction == "Defective":
                labels_pred.append(1)
            else:
                labels_pred.append(0)
            labels_test.append(0)
        else:
            print(f"File_name: {i.split('/')[-1]} Return Code: {response.status_code} Text : {response.text}")
            failure_list.append(i.split('/')[-1])
            continue
    ti.xcom_push(key='augmix_failure_list', value=' '.join(failure_list))
    ti.xcom_push(key='augmix_process_count', value=len(labels_pred))
    labels_pred = np.array(labels_pred, dtype=np.uint8)
    labels_test = np.array(labels_test, dtype=np.uint8)
    cm = tf.math.confusion_matrix(labels_test, labels_pred )

    print("Confusion")
    print(cm)
    print(f"labels_test : {len(labels_test)}")
    print(f"labels_pred : {len(labels_pred)}")
    
    file_name = f"/opt/airflow/working_data/{ts}-UTC_augmix"
    np.save(file_name, cm.numpy())
    file_name = file_name + ".npy"
    # return upload_blob("airflow-run-cm", file_name, file_name.split('/')[-1])
    report_url =  upload_blob("airflow-run-cm", file_name, file_name.split('/')[-1])
    ti.xcom_push(key='aug_file_report', value=report_url)

def upload_blob(bucket_name, source_file_name, destination_blob_name):
    """Uploads a file to the bucket."""
    # The ID of your GCS bucket
    # bucket_name = "your-bucket-name"
    # The path to your file to upload
    # source_file_name = "local/path/to/file"
    # The ID of your GCS object
    # destination_blob_name = "storage-object-name"

    os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = "/opt/airflow/keys/key.json"

    storage_client = storage.Client()
    bucket = storage_client.bucket(bucket_name)
    blob = bucket.blob(destination_blob_name)

    blob.upload_from_filename(source_file_name)

    print(f"File {source_file_name} uploaded to {destination_blob_name}.")
    return f"https://storage.googleapis.com/airflow-run-cm/{destination_blob_name}"
 
def download_and_unzip(ti):
    print('Downloading Test Data Start')

    os.chdir('/opt/airflow/working_data/')
    datadir = "/opt/airflow/working_data/"
    fullfilename = os.path.join(datadir, "test.zip")
    urllib.request.urlretrieve("https://storage.googleapis.com/casting-defect/test.zip", "test.zip")
    shutil.unpack_archive("test.zip", "test")

    print('Downloading Test Data Complete')

def send_email(ti):
    os.environ['SENDGRID_API_KEY'] = "############################"

    cutmix_file_url = ti.xcom_pull(task_ids='process_cutmix', key='cutmix_file_report')
    mixup_file_url = ti.xcom_pull(task_ids='process_mixup', key='mixup_file_report')
    augmix_file_url = ti.xcom_pull(task_ids='process_augmix', key='aug_file_report')

    total_file_count = ti.xcom_pull(task_ids='process_mixup', key='total_file_count')

    cutmix_process_count = ti.xcom_pull(task_ids='process_cutmix', key='cutmix_process_count')
    mixup_process_count = ti.xcom_pull(task_ids='process_mixup', key='mixup_process_count')
    augmix_process_count = ti.xcom_pull(task_ids='process_augmix', key='augmix_process_count')

    cutmix_failure_list = ti.xcom_pull(task_ids='process_cutmix', key='cutmix_failure_list')
    mixup_failure_list = ti.xcom_pull(task_ids='process_mixup', key='mixup_failure_list')
    augmix_failure_list = ti.xcom_pull(task_ids='process_augmix', key='augmix_failure_list') 

    failed_count =  (total_file_count * 3) - (cutmix_process_count + mixup_process_count + augmix_process_count)

    ts = time.strftime("%Y-%m-%d_%H:%M:%S")

    failure_percentage = (failed_count / total_file_count) * 100
    failure_percentage = "{:.2f}".format(failure_percentage)

    message = Mail(
        from_email='anand.pi@northeastern.edu',
        to_emails='anand.pi@northeastern.edu',
        subject=f"Airflow | Batch Report",
        html_content=f"""
<head>
</head>
<body>
   <h1 style="text-align:center;">Airflow Run Report</h1>
   <p> <b> Summary: </b> <br>
      Total :  {total_file_count} <br>
      Failed :  {failed_count} <br> 
      Failed %:  {failure_percentage} 
   </p>
   <p> <b> Report accessible:  </b> <br> 
      Augmix: {augmix_file_url} <br> 
      Mixup: {mixup_file_url}  <br> 
      Cutmix:  {cutmix_file_url}
   </p>
   <p> <b> Failure report list:  </b> <br>  
      Augmix: {augmix_process_count} <br> 
      {augmix_failure_list} <br>
      Mixup: {mixup_process_count} <br> 
      {mixup_failure_list}  <br>
      Cutmix:  {cutmix_process_count} <br> 
      {cutmix_failure_list} <br>
   </p>
   <p> <i> Report generated on {ts} </i> </p>
</body>
""")
    try:
        sg = SendGridAPIClient(os.environ.get('SENDGRID_API_KEY'))
        response = sg.send(message)
        print(response.status_code)
        print(response.body)
        print(response.headers)
    except Exception as e:
        print(e.message)
    




with dag:

    clean_dir = BashOperator(
        task_id="clean_dir",
        bash_command='echo "Cleaning following files" ; ls -l /opt/airflow/working_data ; rm -rf /opt/airflow/working_data/*',
    )

    download_test_data = PythonOperator(
        task_id='download_test_data',
        python_callable = download_and_unzip
    )

    authenticate_to_API = PythonOperator(
        task_id='authenticate_to_API',
        python_callable = authenticate_to_API
    )
 
    process_augmix = PythonOperator(
        task_id='process_augmix',
        python_callable = process_augmix
    )

    process_cutmix = PythonOperator(
        task_id='process_cutmix',
        python_callable = process_cutmix
    )

    process_mixup = PythonOperator(
        task_id='process_mixup',
        python_callable = process_mixup
    )

    send_email = PythonOperator(
        task_id='send_email',
        python_callable = send_email
    )


    clean_dir >> download_test_data  >> authenticate_to_API >> [process_augmix, process_cutmix, process_mixup] >> send_email
    # 