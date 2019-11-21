FROM python:3.7

RUN apt-get update
RUN git clone https://github.com/alan-turing-institute/chance-water-distribution
WORKDIR /chance-water-distribution
RUN git submodule update --init --recursive
RUN pip install -r requirements.txt

CMD bokeh serve --show water
