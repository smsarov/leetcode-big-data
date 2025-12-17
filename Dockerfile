FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        curl \
        gnupg \
        chromium-driver \
        chromium \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt /app/requirements.txt

RUN pip install --no-cache-dir -r requirements.txt

COPY . /app

ENV OUT_DIR=/data/out
ENV HEADLESS=1
ENV CHROME_BINARY=/usr/bin/chromium

ENTRYPOINT ["python", "main.py"]


