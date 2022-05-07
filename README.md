# Intellisite Challenge

[![Kafka](https://img.shields.io/badge/streaming_platform-kafka-black.svg?style=flat-square)](https://kafka.apache.org)
[![Docker Images](https://img.shields.io/badge/docker_images-confluent-orange.svg?style=flat-square)](https://github.com/confluentinc/cp-docker-images)
[![Python](https://img.shields.io/badge/python-3.8-blue.svg?style=flat-square)](https://www.python.org)

## Description

This challenge is fully containerised (you will need [Docker](https://docs.docker.com/install/) and [Docker Compose](https://docs.docker.com/compose/) to run it). 

By running `docker-compose up --build` to start up all services.

The challenge consist in building two microservices, that they are connected through the broker. It have been decided use the following stack for development:

- All microservices are asynchronous using `asyncio`.
- For database storage it uses MongoDB.
- For API application, it uses fastAPI framework.

## Indexer Microservice

This microservice is a Kafka Consumer/Producer. It consumes messages (vehicle detections) from the topic called `intellisite.detections`, indexes the messages in a MongoDB database and generates alerts based on vehicle category filtering by `SUSPICIOUS_VEHICLE` env var (Example: `SUV` category). These alerts are injected in the topic called `intellisite.alerts`.

## Detections API
This API is a microservice developed with FastAPI framework and has the following features:
- Integrate Swagger.
- Implement JWT for authentication.
- POST /users to create the users.
- GET /detections endpoint to expose all detections indexed in the MongoDB database:
    - The response is paginated. Use skip and limit as the pagination query params.
- GET /stats to return vehicle counting per Make (group_by).
- GET /alerts endpoint to receive the alerts in real-time:
    - This endpoint is an event stream.
    - A Kafka Consumer inside the API consumes the alerts and expose them through this event-stream endpoint.

## Project Setup

- Spin up all services by running:

```bash
$ docker-compose up -d
```

It'll start up:

- Kafka broker and zookeeper.
- KafDrop: a web UI for viewing kafka topics and message. See http://localhost:9000
- Producer: an async app for producing fake vehicle detection events.
- Indexer: an async app that listening the topic for vehicle detection events and store them and alert when find a kind of vehicle specified
- API: a fastAPI app with several endpoints specified above. It runs on http://localhost:8000 (API documentation on `/docs`)

## How to watch the broker messages

Show a stream of detections in the topic `intellisite.detections` (optionally add `--from-beginning`):

```bash
$ docker-compose -f docker/docker-compose.kafka.yml exec broker kafka-console-consumer --bootstrap-server localhost:9092 --topic intellisite.detections
```

Also, you can use KafDrop in http://localhost:9000/.

Topics:

- `intellisite.detections`: raw generated detections
- `intellisite.alerts`: alerts for suspicious vehicles (filter by Category: all SUV will be suspicious vehicles)

Examples detection message:

```json
{
   "year": 1999,
   "make": "Cadillac",
   "model": "Escalade",
   "category": "SUV",
   "created_at": "2022-05-07T04:51:08.381523"
}
```

## How to check event-stream `/alerts` endpoint

First, you need a valid user:

```bash
curl -X 'POST' \
  'http://localhost:8000/users' \
  -H 'accept: application/json' \
  -H 'Content-Type: application/json' \
  -d '{
  "username": "matuu",
  "password": "123456",
  "email": "hi@matuu.dev",
  "full_name": "Matu Varela"
}'
```

Now, you need a JWT token to interact with the API:

```bash
curl -X 'POST' \
  'http://localhost:8000/token' \
  -H 'accept: application/json' \
  -H 'Content-Type: application/x-www-form-urlencoded' \
  -d 'grant_type=&username=matuu&password=123456&scope=&client_id=&client_secret='
```

It'll return a valid token like:

```bash
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJtYXR1dSIsImV4cCI6MTY1MTkwNDA2N30.GQKzLibrURtZqeFT1eDVSzVAz-qJW5FHp3eTKXn5zO4",
  "token_type": "bearer"
}
```

With this token, you can request alerts in real-time:

```bash
curl -X 'GET' \
  'http://localhost:8000/stats' \
  -H 'accept: application/json' \
  -H 'Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJtYXR1dSIsImV4cCI6MTY1MTkwNDA2N30.GQKzLibrURtZqeFT1eDVSzVAz-qJW5FHp3eTKXn5zO4'
```

**Note: this endpoint don't work well in Swagger