FROM python:3.8

COPY requirements.txt /src/app/
RUN pip install -r /src/app/requirements.txt

WORKDIR /src/app
COPY . .

# CMD  ["uvicorn", "app.main:app", "--reload", "--host", "0.0.0.0"]
CMD  ["uvicorn", "main:app", "--host", "0.0.0.0"]

