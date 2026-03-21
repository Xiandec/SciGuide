FROM python:3.13-slim

WORKDIR /app

# Установка внутренней библиотеки из исходников монорепы
COPY packages/sciguide_pipeline_pipeline /tmp/sciguide_pipeline
RUN pip install --no-cache-dir /tmp/sciguide_pipeline \
    && rm -rf /tmp/sciguide_pipeline

# Установка зависимостей сервиса
COPY src/backend/requirements.txt ./requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Копирование исходного кода сервиса
COPY src/backend/ .

CMD ["python", "-m", "main"]
