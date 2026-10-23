FROM python:3.12-slim
RUN pip install --no-cache-dir paho-mqtt==2.1.0
WORKDIR /app
COPY publisher.py force_alert.py /app/
CMD ["python", "-u", "publisher.py"]
