# Use an official Python runtime as a parent image
FROM python:3.9.3-slim

# Install git
RUN apt-get update && apt-get install -y git
RUN pip install --upgrade pip

# Set the working directory in the container
WORKDIR /app

COPY ./src/requirements.txt /app/requirements.txt

RUN pip install --no-cache-dir -r requirements.txt

COPY ./src /app

CMD ["trunk_monkey", "init"]