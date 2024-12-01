FROM python:3.10-slim

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    python3-dev \
    python3-pip \
    python3-cffi \
    libcairo2 \
    libpango-1.0-0 \
    libpangocairo-1.0-0 \
    libgdk-pixbuf2.0-0 \
    shared-mime-info \
    libffi-dev \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .

# Create an entrypoint script
RUN echo '#!/bin/sh\n\
uvicorn app.main:app --host 0.0.0.0 --port 8000\n'\
> ./entrypoint.sh && chmod +x ./entrypoint.sh

# Use the entrypoint script
ENTRYPOINT ["./entrypoint.sh"]