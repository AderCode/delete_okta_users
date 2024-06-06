FROM ubuntu:20.04

ENV DEBIAN_FRONTEND noninteractive

COPY ./src /okta-user-deletion

WORKDIR /okta-user-deletion

ARG AWS_ACCESS_KEY_ID
ARG AWS_SECRET_ACCESS_KEY
ARG AWS_DEFAULT_REGION

RUN apt update
RUN apt-get update
RUN apt-get install -y python3-pip
RUN python3 -m pip install pip --upgrade
RUN pip install -r app/requirements.txt
RUN aws configure set aws_access_key_id $AWS_ACCESS_KEY_ID
RUN aws configure set aws_secret_access_key $AWS_SECRET_ACCESS_KEY
RUN aws configure set region $AWS_DEFAULT_REGION

# CMD ["tail", "-f", "/dev/null"] # Keep container open and running to allow manual execution
CMD ["python3", "-m", "app.main"] # Auto run script.py when container starts