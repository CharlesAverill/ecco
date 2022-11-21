# ecco
An `Educational C COmpiler` written in Python, written for use in my Practical Compiler Design course.

## Installation

A Docker image is provided for non-Linux users, although usage of Linux to proceed through this course is strongly encouraged for many unrelated reasons.

1. Download the git repository:
    ```bash
    git clone https://github.com/CharlesAverill/ecco.git
    cd ecco
    ```

2. Install Docker:
    - [Windows](https://docs.docker.com/docker-for-windows/install/)
    - [Mac](https://docs.docker.com/docker-for-mac/install/)
    - [Linux](https://docs.docker.com/install/linux/docker-ce/ubuntu/)

3. Build the base image:
    ```bash
    make dbuild
    ```

## Development Usage

The [Makefile](./Makefile) contains commands to run the `ecco` compiler inside and outside of the Docker image.

- `make dbuild` - Build the Docker image
- `make drun` - Run the compiler within the Docker image built with `make dbuild`
- `make dbuildrun` - Build and run the Docker image and compiler
- `make run` - Runs the compiler with [poetry](https://python-poetry.org/)
- `make install` - Installs your compiler with the default `pip` 

