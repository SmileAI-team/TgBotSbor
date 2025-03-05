FROM python:3.9-slim

WORKDIR /app

RUN apt-get update && apt-get install -y \
    libpq-dev \
    gcc \
    && rm -rf /var/lib/apt/lists/*

COPY save/requirements.txt ./save/requirements.txt
RUN pip install --no-cache-dir -r save/requirements.txt

COPY save/ ./save/

CMD ["python", "-m", "save.main"]