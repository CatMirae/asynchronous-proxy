FROM python:2.7

COPY . /code
WORKDIR /code

RUN apt-get update -y

RUN apt-get -y install \
    python-dev \
    libffi-dev \
    libssl-dev \
    python-pip

RUN pip install -r requirements.txt

# Default port
ENV PROXY_PORT=8080

CMD python castlabs_proxy.py
