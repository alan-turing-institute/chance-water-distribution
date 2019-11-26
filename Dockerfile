FROM python:3.7

RUN apt-get update
COPY water /water
COPY requirements.txt /requirements.txt

RUN pip install -r requirements.txt

CMD bokeh serve water
