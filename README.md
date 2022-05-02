# Intellisite Challenge

[![Kafka](https://img.shields.io/badge/streaming_platform-kafka-black.svg?style=flat-square)](https://kafka.apache.org)
[![Docker Images](https://img.shields.io/badge/docker_images-confluent-orange.svg?style=flat-square)](https://github.com/confluentinc/cp-docker-images)
[![Python](https://img.shields.io/badge/python-3.8-blue.svg?style=flat-square)](https://www.python.org)

## Description

This challenge should be fully containerised, and it must be uploaded to a repository with its respective README.md with the deployment instructions.

You will need [Docker](https://docs.docker.com/install/) and [Docker Compose](https://docs.docker.com/compose/) to run it.

You simply need to create a Docker network called `intellisite` to enable communication between the Kafka broker and all microservices.

The challenge consist in building two microservices, that they are connected through the broker:

## Indexer Microservice

This microservice should be a Kafka Consumer/Producer. It should have to consume messages (vehicle detections) from the topic called `intellisite.detections`, index the messages in a database (free election) and generate alerts based on vehicle category filtering by `SUSPICIOUS_VEHICLE` env var (Example: `SUV` category). These alerts should be injected in the topic called `intellisite.alerts`.

## Detections API
Develop the following features:
- Integrate Swagger.
- Implement JWT for authentication.
- POST /users to create the users.
- Develop GET /detections endpoint to expose all detections indexed in the database you chose in Indexer Microservice:
    - The response should be paginated. Use skip and limit as the pagination query params.
- Develop GET /stats to return vehicle counting per Make (group_by).
- Develop GET /alerts endpoint to receive the alerts in real-time:
    - This endpoint should be an event stream.
    - Develop a Kafka Consumer inside the API to consume the alerts and expose them through the /alerts event-stream endpoint.

## Producer Setup

- Spin up the local single-node Kafka cluster (will run in the background):

```bash
$ docker-compose -f docker/docker-compose.kafka.yml up -d
```

- Check the cluster is up and running (wait for "started" to show up):

```bash
$ docker-compose -f docker/docker-compose.kafka.yml logs -f broker | grep "started"
```

- Start the detections producer (will run in the background):

```bash
$ docker-compose -f docker/docker-compose.producer.yml up -d
```

## How to watch the broker messages

Show a stream of detections in the topic `intellisite.detections` (optionally add `--from-beginning`):

```bash
$ docker-compose -f docker/docker-compose.kafka.yml exec broker kafka-console-consumer --bootstrap-server localhost:9092 --topic intellisite.detections
```

Topics:

- `intellisite.detections`: raw generated detections
- `intellisite.alerts`: alerts for suspicious vehicles (filter by Category: all SUV will be suspicious vehicles)

Examples detection message:

```json
{'Year': 2011, 'Make': 'Toyota', 'Model': 'Land Cruiser', 'Category': 'SUV'}
```

## Teardown

To stop the detections producer:

```bash
$ docker-compose -f docker/docker-compose.producer.yml down
```

To stop the Kafka cluster (use `down`  instead to also remove contents of the topics):

```bash
$ docker-compose -f docker-compose.kafka.yml stop
```

To remove the Docker network:

```bash
$ docker network rm intelliste
```
