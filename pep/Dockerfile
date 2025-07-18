FROM python:3.10-slim

WORKDIR /app

COPY app.py .
COPY policies.json .

RUN pip install flask requests psycopg2-binary python-dotenv

CMD ["python", "app.py"]