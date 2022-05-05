FROM python:3.8

COPY requirements.txt /usr/app/
RUN pip install -r /usr/app/requirements.txt

WORKDIR /usr/app
COPY . .

CMD  ["uvicorn", "app.main:app", "--reload", "--host", "0.0.0.0"]

