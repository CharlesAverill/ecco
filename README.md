# ecco
An `Educational C COmpiler` written in Python, written for use in my Practical Compiler Design course.

## Installation

A Docker image is provided for non-Linux users, although usage of Linux to proceed through this course is strongly encouraged for many unrelated reasons.

1. Download the git repository:
    ```bash
    git clone https://github.com/CharlesAverill/ecco.git
    cd ecco
    ```
### With Docker

2. Install Docker:
    - [Windows](https://docs.docker.com/docker-for-windows/install/)
    - [Mac](https://docs.docker.com/docker-for-mac/install/)
    - [Linux](https://docs.docker.com/install/linux/docker-ce/ubuntu/)

3. Build the base image:
    ```bash
    ./scripts dbuild
    ```

### Without Docker

2. Install [poetry](https://python-poetry.org/)
    ```bash
    python -m pip install poetry
    ```

3. Install project dependencies
    ```bash
    poetry install
    ```

## Development Usage

The [scripts](./scripts) file contains commands to run the `ecco` compiler inside and outside of the Docker image.

- `./scripts dbuild` - Build the Docker image
- `./scripts drun` - Run the compiler within the Docker image built with `./scripts dbuild`
- `./scripts dbuildrun` - Build and run the Docker image and compiler
- `./scripts run` - Runs the compiler with [poetry](https://python-poetry.org/)
- `./scripts install` - Installs your compiler with the default `pip` 

