# FROM ubuntu:16.04
FROM python:3.8

RUN apt-get -y update
RUN pip install bottle gunicorn requests numpy tables
RUN pip install --no-binary :all: pandas 

COPY ./src /oiip-point-decimator

COPY ./lib/ulttb /ulttb

WORKDIR /ulttb

RUN python setup.py install

WORKDIR /oiip-point-decimator

EXPOSE 8101
CMD ["python", "./server.py"]
