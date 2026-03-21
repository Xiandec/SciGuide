# SciGuide notebooks

В этой директории лежит базовый ноутбук для демонстрации библиотеки
`sciguide_pipeline` на датасете `BEIR SciFact`.

## Что поднять перед запуском ноутбука

Для ноутбука достаточно двух сервисов:

- `qdrant`
- `neo4j`

Backend, PostgreSQL, Redis и Flyway для этого сценария не нужны.

Запуск из корня репозитория:

```bash
docker compose -f notebooks/docker-compose.notebook.yml up -d
```

## Локальные файлы

- `notebooks/.env` содержит только `OPENROUTER_API_KEY`
- `notebooks/data/` содержит датасет, кеш моделей и локальные данные сервисов

Оба пути исключены из git через `notebooks/.gitignore`.
