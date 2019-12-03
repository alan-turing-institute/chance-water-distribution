FROM python:3.7

RUN apt-get update
COPY water /water
COPY requirements.txt /requirements.txt

RUN pip install -r requirements.txt
RUN pip install gunicorn

WORKDIR /water
EXPOSE 8000
CMD ["gunicorn", "-b", "0.0.0.0:8000", "-w", "4", "main:app"]
