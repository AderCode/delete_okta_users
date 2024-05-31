FROM python:3.9-slim
COPY ./src /app
COPY ./requirements.txt /app

WORKDIR /app
RUN apt-get update
RUN python -m pip install pip --upgrade
RUN pip install -r requirements.txt

CMD ["tail", "-f", "/dev/null"] # Keep container open and running to allow manual execution
# CMD ["python", "script.py"] # Auto run script.py when container starts