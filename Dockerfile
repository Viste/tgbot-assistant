FROM python:3.9-slim-buster

WORKDIR /app

COPY . /app

EXPOSE 5000

RUN mkdir -p /app/logs

RUN pip install --no-cache-dir -r requirements.txt

CMD ["python", "main.py"]
