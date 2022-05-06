FROM python:3.8

WORKDIR /usr/src

ADD requirements.txt /usr/src
RUN pip install -r requirements.txt
ADD . /usr/src

CMD ["python3", "app/main.py"]
