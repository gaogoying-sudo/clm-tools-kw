FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

COPY app/data-sync/requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r /app/requirements.txt

COPY app/data-sync /app/app/data-sync
COPY dataenv.txt /app/dataenv.txt

EXPOSE 8000

CMD ["python", "/app/app/data-sync/api_server.py"]
