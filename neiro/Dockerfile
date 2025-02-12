FROM python:3.9-slim

WORKDIR /app

# Устанавливаем системные зависимости для opencv
RUN apt-get update && apt-get install -y \
    libgl1-mesa-glx \
    libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

# Сначала копируем только requirements.txt для neiro
COPY neiro/requirements.txt ./neiro/requirements.txt
RUN pip install --no-cache-dir -r neiro/requirements.txt

# Затем копируем остальной код
COPY neiro/ ./neiro/

# Запускаем модуль neiro
CMD ["python", "-m", "neiro.rabbitmq_worker"]
