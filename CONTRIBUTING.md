# Работа с Git

## Ветки

Основная ветка: `main`

Создаём ветку от актуального `main`:

```bash
git checkout main && git pull
git checkout -b <тип>/<описание>
```

| Тип        | Когда использовать      | Пример                   |
| ---------- | ----------------------- | ------------------------ |
| `feature/` | Новая функциональность  | `feature/user-auth`      |
| `bugfix/`  | Исправление ошибок      | `bugfix/header-overflow` |
| `hotfix/`  | Критические правки      | `hotfix/db-connection`   |
| `chore/`   | Техзадачи, документация | `chore/update-deps`      |

---

## Коммиты

Формат: `тип(область): описание`

```bash
git commit -m "feat(scheduler): добавить оптимизацию слотов"
```

| Тип        | Что меняем                          |
| ---------- | ----------------------------------- |
| `feat`     | Новая функция                       |
| `fix`      | Исправление бага                    |
| `docs`     | Документация                        |
| `test`     | Тесты                               |
| `chore`    | Конфиги, зависимости                |
| `refactor` | Рефакторинг без изменения поведения |

---

## Workflow

```bash
# 1. Начать работу
git checkout main && git pull
git checkout -b feature/my-feature

# 2. Закоммитить
git add .
git commit -m "feat(api): добавить endpoint"

# 4. Запушить и создать PR
git push -u origin feature/my-feature
```

PR делаем в `main`. Прямые пуши в `main` запрещены.

---

## Правила

- Один PR = одна задача
- Перед пушем: `pytest tests/test_flake8.py`
- `git push --force` — только после согласования
