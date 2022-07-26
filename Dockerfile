FROM apache/airflow:2.3.3

USER root

RUN apt-get update \
  && apt-get install -y wget \
  && apt-get install -y unzip \
  && apt-get install -y git \
  && rm -rf /var/lib/apt/lists/*

USER airflow

COPY requirements.txt /requirements.txt

RUN pip install --user --upgrade pip

RUN pip install --no-cache-dir --user -r /requirements.txt