FROM python:3.10-slim

WORKDIR /app

COPY app.py .

RUN pip install flask requests python-dotenv

CMD ["python", "app.py"]