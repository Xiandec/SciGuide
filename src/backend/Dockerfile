FROM python:3.13-slim

WORKDIR /app

# Установка зависимостей сервиса
COPY backend/requirements.txt ./requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Установка внутренней библиотеки из исходников монорепы
COPY packages /tmp/sciguide_pipeline
RUN pip install --no-cache-dir /tmp/sciguide_pipeline \
    && rm -rf /tmp/sciguide_pipeline

# Копирование исходного кода сервиса
COPY backend/ .

CMD ["python", "-m", "main"]
