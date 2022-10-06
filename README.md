# kobo2espo
Connector between KoBo and EspoCRM.

Developed in support to the [Ukraine crisis 2022](https://go.ifrc.org/emergencies/5854).

## Description

Synopsis: a [dockerized](https://www.docker.com/) [python app](https://www.python.org/) that sends KoBo submissions to EspoCRM.

Worflow: push a specific submission and its attachments from KoBo to EspoCRM.

## Setup
Generic requirements:
- a deployed KoBo form
- a running EspoCRM instance
- the mapping of fields from KoBo to EspoCRM (as .csv uder `data/`)
- all necessary credentials (as .env under `credentials/`)

### with Docker
1. Install [Docker](https://www.docker.com/get-started)
2. Build the docker image from the root directory
```
docker build -t rodekruis/kobo2espo .
```
3. Run the docker image in a new container and access it
```
docker run -it --entrypoint /bin/bash rodekruis/kobo2espo
```
4. Check that everything is working by running the pipeline (see [Usage](https://github.com/rodekruis/espo2redrose#usage) below)

### Manual Setup
TBI

## Usage
Command:
```
kobo2espo [OPTIONS]
```
Options:
  ```
  --koboid                    ID of the KoBo submission
  --verbose                   print more output
  --help                      show this message and exit
  ```
