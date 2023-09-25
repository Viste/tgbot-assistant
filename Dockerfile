FROM python:3.9-slim-buster

ENV DB_HOST your_db_host
ENV DB_PORT your_db_port
ENV DB_NAME your_db_name
ENV DB_USER your_db_user
ENV DB_PASSWORD your_db_password

WORKDIR /app

COPY . /app

RUN pip install --no-cache-dir -r requirements.txt

CMD ["python", "main.py"]
