---
applyTo: '**'
---
# Руководство по архитектуре проекта (Clean Architecture)

## Общая структура проекта

```
src/backend/
├── domain/              # Доменный слой (бизнес-логика)
├── application/         # Слой приложения (use cases)
├── infrastructure/      # Слой инфраструктуры (внешние сервисы)
├── presentation/        # Слой представления (API, endpoints)
├── auth/               # Утилиты аутентификации
├── config.py           # Конфигурация приложения
└── main.py             # Точка входа приложения
```

---

## 1. Domain Layer (`domain/`)

**Цель**: Содержит бизнес-логику, независимую от внешних зависимостей. Это ядро приложения.

### 1.1 Entities (`domain/entities/`)

**Что хранится**: Доменные сущности - объекты бизнес-логики с поведением.

**Правила**:

- Используйте `@dataclass` для определения структуры
- Храните бизнес-правила и валидацию внутри сущности
- НЕ зависьте от фреймворков (FastAPI, SQLAlchemy и т.д.)
- Методы сущности должны отражать бизнес-операции, а не технические детали

**Структура файла**:

```python
# domain/entities/user.py
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from uuid import UUID

class SubscriptionStatus(Enum):
    """Enum для статусов - часть домена"""
    FREE = "free"
    TRIAL = "trial"
    PREMIUM = "premium"

@dataclass
class User:
    """Доменная сущность с бизнес-логикой"""
    id: UUID
    full_name: str
    email: str
    password_hash: str
    subscription_status: SubscriptionStatus
    # ... другие поля

    def __post_init__(self):
        """Валидация при создании"""
        if not self.email.strip():
            raise ValueError("Email не может быть пустым")

    def is_subscription_active(self) -> bool:
        """Бизнес-метод"""
        # ... логика

    def update_profile(self, full_name: str, email: str):
        """Изменение состояния сущности"""
        # ... валидация и обновление
```

**Именование**:

- Файл: `<entity_name>.py` (например, `user.py`, `post.py`)
- Класс: PascalCase (`User`, `Post`, `Resource`)
- Один файл = одна основная сущность + связанные enums

---

### 1.2 Repositories (Интерфейсы) (`domain/repositories/`)

**Что хранится**: Абстрактные интерфейсы для работы с данными.

**Правила**:

- Используйте `ABC` и `@abstractmethod`
- Определяйте только сигнатуры методов
- Методы оперируют доменными сущностями, не DTO
- НЕ содержат реализации (только контракты)

**Структура файла**:

```python
# domain/repositories/user_repository.py
from abc import ABC, abstractmethod
from typing import Optional, List, Tuple
from uuid import UUID
from ..entities.user import User, SubscriptionStatus

class UserRepository(ABC):
    """Интерфейс репозитория пользователей"""

    @abstractmethod
    async def create(self, user: User) -> User:
        """Создать пользователя"""
        pass

    @abstractmethod
    async def get_by_id(self, user_id: UUID) -> Optional[User]:
        """Получить по ID"""
        pass

    @abstractmethod
    async def list(
        self,
        limit: int = 10,
        offset: int = 0
    ) -> Tuple[List[User], int]:
        """Список с пагинацией"""
        pass
```

**Именование**:

- Файл: `<entity>_repository.py` (например, `user_repository.py`)
- Класс: `<Entity>Repository` (например, `UserRepository`)
- Методы: CRUD + специфичные для бизнеса (`exists_by_email`, `get_active_subscriptions`)

---

### 1.3 Exceptions (`domain/exceptions/`)

**Что хранится**: Доменные исключения для бизнес-ошибок.

**Правила**:

- Наследуйтесь от базового доменного исключения
- Исключения должны быть понятны бизнесу
- Содержат только бизнес-логику ошибок, не технические детали

**Структура файла**:

```python
# domain/exceptions/user_exceptions.py
from typing import Optional

class UserDomainError(Exception):
    """Базовое исключение домена пользователей"""
    pass

class UserNotFoundError(UserDomainError):
    """Пользователь не найден"""
    def __init__(self, user_id: Optional[str] = None):
        message = f"Пользователь с ID {user_id} не найден"
        super().__init__(message)

class UserAlreadyExistsError(UserDomainError):
    """Пользователь уже существует"""
    def __init__(self, email: str):
        message = f"Пользователь с email {email} уже существует"
        super().__init__(message)
```

**Именование**:

- Файл: `<entity>_exceptions.py` (например, `user_exceptions.py`)
- Класс: `<Entity><ErrorType>Error` (например, `UserNotFoundError`)
- Базовое исключение: `<Entity>DomainError`

---

## 2. Application Layer (`application/`)

**Цель**: Содержит use cases (сценарии использования) - оркестрация бизнес-логики.

### 2.1 Use Cases (`application/use_cases/<entity>/`)

**Что хранится**: Классы use cases, которые координируют работу с репозиториями и сущностями.

**Правила**:

- Один use case = одна бизнес-операция
- Use case зависит только от интерфейсов репозиториев (не реализаций)
- Принимает запрос (Request DTO), возвращает ответ (Response DTO)
- Содержит оркестрацию, но не бизнес-правила (они в entities)

**Структура папки**:

```
application/use_cases/
└── user/
    ├── __init__.py
    ├── dto.py                    # Общие DTO для модуля
    ├── register_user.py          # Use case регистрации
    ├── login_user.py             # Use case входа
    ├── get_user.py               # Use case получения
    ├── update_user.py            # Use case обновления
    └── _token_utils.py           # Вспомогательные утилиты (начинаются с _)
```

**Структура use case файла**:

```python
# application/use_cases/user/register_user.py
from dataclasses import dataclass
from uuid import UUID, uuid4
from datetime import datetime

from domain.entities import User, SubscriptionStatus
from domain.repositories import UserRepository
from domain.exceptions import UserAlreadyExistsError

@dataclass
class RegisterUserRequest:
    """DTO для входных данных"""
    full_name: str
    email: str
    password: str

@dataclass
class RegisterUserResponse:
    """DTO для выходных данных"""
    user_id: UUID
    email: str
    access_token: str

class RegisterUser:
    """Use case регистрации пользователя"""

    def __init__(self, user_repository: UserRepository):
        """Зависимости через конструктор"""
        self._user_repository = user_repository

    async def execute(self, request: RegisterUserRequest) -> RegisterUserResponse:
        """Основной метод выполнения"""
        # 1. Валидация (может делегироваться в domain)
        if len(request.password) < 8:
            raise WeakPasswordError()

        # 2. Проверка бизнес-правил
        if await self._user_repository.exists_by_email(request.email):
            raise UserAlreadyExistsError(request.email)

        # 3. Создание доменной сущности
        user = User(
            id=uuid4(),
            full_name=request.full_name,
            email=request.email,
            password_hash=hash_password(request.password),
            subscription_status=SubscriptionStatus.TRIAL,
            created_at=datetime.now(),
            updated_at=datetime.now()
        )

        # 4. Сохранение через репозиторий
        created_user = await self._user_repository.create(user)

        # 5. Возврат DTO
        return RegisterUserResponse(
            user_id=created_user.id,
            email=created_user.email,
            access_token=generate_token(created_user)
        )
```

**Именование**:

- Файл: `<action>_<entity>.py` (например, `register_user.py`, `fetch_feed.py`)
- Класс use case: `<Action><Entity>` (например, `RegisterUser`, `FetchFeed`)
- Request DTO: `<UseCaseName>Request`
- Response DTO: `<UseCaseName>Response`
- Метод выполнения: `execute()`

---

### 2.2 DTO (`application/use_cases/<entity>/dto.py`)

**Что хранится**: Общие DTO (Data Transfer Objects) для use cases модуля.

**Правила**:

- Используйте `@dataclass` или Pydantic `BaseModel`
- DTO для передачи данных между слоями
- Могут дублировать структуру entities, но с другой целью
- Не содержат бизнес-логики

**Структура файла**:

```python
# application/use_cases/user/dto.py
from dataclasses import dataclass
from datetime import datetime
from uuid import UUID

@dataclass
class UserResponseDTO:
    """Общий DTO для ответа с данными пользователя"""
    id: UUID
    full_name: str
    email: str
    subscription_status: str  # строковое представление enum
    created_at: datetime
    updated_at: datetime
```

---

## 3. Infrastructure Layer (`infrastructure/`)

**Цель**: Реализации интерфейсов репозиториев и работа с внешними сервисами.

### 3.1 Repositories (`infrastructure/repositories/`)

**Что хранится**: Конкретные реализации интерфейсов репозиториев.

**Правила**:

- Реализуют интерфейсы из `domain/repositories/`
- Содержат технические детали (SQL, API запросы и т.д.)
- Конвертируют данные между внешним форматом и доменными сущностями
- Одна реализация = одна технология (Postgres, Redis, HTTP API)

**Структура файла**:

```python
# infrastructure/repositories/postgres_user_repository.py
import asyncpg
from typing import Optional, List, Tuple
from uuid import UUID

from domain.entities import User, SubscriptionStatus
from domain.repositories import UserRepository
from domain.exceptions import UserAlreadyExistsError, UserNotFoundError

class PostgresUserRepository(UserRepository):
    """Реализация репозитория через PostgreSQL"""

    def __init__(self, pool: asyncpg.Pool):
        """Зависимости БД через конструктор"""
        self._pool = pool

    async def create(self, user: User) -> User:
        """Реализация создания"""
        query = """
            INSERT INTO users (id, full_name, email, ...)
            VALUES ($1, $2, $3, ...)
            RETURNING *
        """
        try:
            row = await self._pool.fetchrow(query, user.id, user.full_name, ...)
        except asyncpg.UniqueViolationError as exc:
            raise UserAlreadyExistsError(user.email) from exc

        return self._row_to_user(row)

    def _row_to_user(self, row: asyncpg.Record) -> User:
        """Конвертация DB row -> доменная сущность"""
        return User(
            id=row["id"],
            full_name=row["full_name"],
            email=row["email"],
            subscription_status=SubscriptionStatus(row["subscription_status"]),
            # ...
        )
```

**Именование**:

- Файл: `<technology>_<entity>_repository.py` (например, `postgres_user_repository.py`, `redis_blacklist_repository.py`)
- Класс: `<Technology><Entity>Repository` (например, `PostgresUserRepository`)
- Приватные методы конвертации: `_row_to_<entity>()`, `_<entity>_to_row()`

---

### 3.2 External Services (`infrastructure/resourse_scrapper/`, etc.)

**Что хранится**: Классы для работы с внешними API, парсерами и т.д.

**Правила**:

- Группируйте по типу сервиса (scrapper, api_clients, и т.д.)
- Используйте базовые классы для общей логики
- Изолируйте технические детали от бизнес-логики

**Структура**:

```
infrastructure/
├── repositories/        # Реализации репозиториев
├── resourse_scrapper/   # Парсеры RSS, каналов и т.д.
│   ├── base.py          # Базовый класс
│   └── rss_getter.py    # Конкретная реализация
└── api_clients/         # HTTP клиенты для внешних API
```

---

## 4. Presentation Layer (`presentation/`)

**Цель**: Слой взаимодействия с внешним миром (API endpoints).

### 4.1 API Endpoints (`presentation/api/endpoints/`)

**Что хранится**: FastAPI endpoints, маршрутизаторы.

**Правила**:

- Один файл = один ресурс (users, posts, resources)
- Endpoints только делегируют работу use cases
- Конвертируют Pydantic схемы в DTO use cases
- Обрабатывают доменные исключения → HTTP статусы

**Структура файла**:

```python
# presentation/api/endpoints/users.py
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status

from domain.exceptions import UserNotFoundError, UserAlreadyExistsError
from application.use_cases.user.register_user import (
    RegisterUser, RegisterUserRequest
)
from ..dependencies import get_register_user_use_case
from ...schemas.user_schemas import UserRegister, RegisterResponse

router = APIRouter(tags=["auth"], prefix="/auth")

@router.post(
    "/register",
    response_model=RegisterResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Регистрация пользователя"
)
async def register(
    user_data: UserRegister,  # Pydantic схема
    use_case: RegisterUser = Depends(get_register_user_use_case),
) -> RegisterResponse:
    """Документация endpoint"""
    try:
        # Конвертация Pydantic -> DTO
        request = RegisterUserRequest(
            full_name=user_data.full_name,
            email=user_data.email,
            password=user_data.password,
        )

        # Выполнение use case
        response_data = await use_case.execute(request)

        # Конвертация DTO -> Pydantic для ответа
        return RegisterResponse(...)

    except UserAlreadyExistsError as e:
        # Обработка доменных исключений
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(e)
        ) from e
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        ) from e
```

**Именование**:

- Файл: `<entity_plural>.py` (например, `users.py`, `posts.py`, `resources.py`)
- Router переменная: `router`
- Функции: snake_case, глаголы REST (`register`, `login`, `get_user_by_id`)

---

### 4.2 Dependencies (`presentation/api/dependencies.py`)

**Что хранится**: Dependency injection для FastAPI (фабрики use cases, репозиториев).

**Правила**:

- Один файл для всех зависимостей проекта
- Функции возвращают экземпляры классов
- Используйте `@lru_cache` для синглтонов
- Четкая иерархия: БД → репозитории → use cases

**Структура файла**:

```python
# presentation/api/dependencies.py
from functools import lru_cache
from fastapi import Depends, Request
import asyncpg

from domain.repositories import UserRepository
from infrastructure.repositories import PostgresUserRepository
from application.use_cases.user.register_user import RegisterUser

# 1. Зависимости инфраструктуры (БД, Redis)
def get_db_pool(request: Request) -> asyncpg.Pool:
    """Получить пул БД из состояния приложения"""
    pool = getattr(request.app.state, "db_pool", None)
    if pool is None:
        raise RuntimeError("Database pool is not initialized")
    return pool

# 2. Зависимости репозиториев
def get_user_repository(
    pool: asyncpg.Pool = Depends(get_db_pool)
) -> UserRepository:
    """Создать репозиторий пользователей"""
    return PostgresUserRepository(pool)

# 3. Зависимости use cases
def get_register_user_use_case(
    user_repository: UserRepository = Depends(get_user_repository)
) -> RegisterUser:
    """Создать use case регистрации"""
    return RegisterUser(user_repository=user_repository)
```

**Именование**:

- Функции: `get_<component_name>` (например, `get_user_repository`, `get_register_user_use_case`)

---

### 4.3 Schemas (`presentation/schemas/`)

**Что хранится**: Pydantic модели для валидации запросов/ответов API.

**Правила**:

- Используйте Pydantic BaseModel
- Описывают контракт API, не бизнес-логику
- Могут содержать валидаторы для формата данных
- Отдельные схемы для Request и Response

**Структура файла**:

```python
# presentation/schemas/user_schemas.py
from datetime import datetime
from uuid import UUID
from typing import Optional
from enum import Enum
from pydantic import BaseModel, Field, validator

class SubscriptionStatus(str, Enum):
    """Enum для API (может дублировать доменный)"""
    FREE = "free"
    TRIAL = "trial"
    PREMIUM = "premium"

class UserRegister(BaseModel):
    """Схема запроса регистрации"""
    full_name: str = Field(..., min_length=1, max_length=255)
    email: str = Field(..., min_length=5, max_length=254)
    password: str = Field(..., min_length=8, max_length=100)

    @validator("email")
    @classmethod
    def validate_email(cls, v):
        """Валидация формата"""
        if "@" not in v:
            raise ValueError("Некорректный email")
        return v

class UserResponse(BaseModel):
    """Схема ответа с данными пользователя"""
    id: UUID
    full_name: str
    email: str
    subscription_status: SubscriptionStatus
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

class RegisterResponse(BaseModel):
    """Схема ответа регистрации"""
    user: UserResponse
    access_token: str
```

**Именование**:

- Файл: `<entity>_schemas.py` (например, `user_schemas.py`)
- Класс запроса: `<Entity><Action>` (например, `UserRegister`, `UserUpdate`)
- Класс ответа: `<Entity>Response` или `<Action>Response` (например, `UserResponse`, `RegisterResponse`)

---

## 5. Auth (`auth/`)

**Что хранится**: Утилиты для аутентификации и авторизации.

**Правила**:

- Не является частью чистой архитектуры (вспомогательный модуль)
- Содержит технические утилиты
- Может использоваться разными слоями

**Структура**:

```
auth/
├── password.py    # Хеширование паролей
├── token.py       # Генерация/валидация JWT
└── header.py      # Извлечение данных из заголовков
```

---

## 6. Configuration (`config.py`)

**Что хранится**: Конфигурация приложения через переменные окружения.

**Правила**:

- Используйте Pydantic Settings
- Одна глобальная переменная `settings`
- Группируйте по категориям (БД, Redis, Auth)

**Структура файла**:

```python
# config.py
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    """Настройки приложения"""
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    # Общие
    debug: bool = False
    host: str = "0.0.0.0"
    port: int = 8000

    # База данных
    POSTGRES_DB: str = "librand_db"
    POSTGRES_USER: str = "user"
    POSTGRES_PASSWORD: str = "password"
    POSTGRES_HOST: str = "db"
    POSTGRES_PORT: int = 5432

    # Redis
    REDIS_HOST: str = "redis"
    REDIS_PORT: int = 6379

    # Auth
    SECRET_KEY: str = "your-secret-key"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30

settings = Settings()
```

---

## 7. Entry Point (`main.py`)

**Что хранится**: Точка входа FastAPI приложения.

**Правила**:

- Создание FastAPI app
- Lifespan для инициализации ресурсов (БД, Redis)
- Подключение роутеров
- Минимум логики

**Структура файла**:

```python
# main.py
from contextlib import asynccontextmanager
from fastapi import FastAPI
import asyncpg

from config import settings
from presentation.api.endpoints import (
    user_router,
    resource_router,
    post_router
)

@asynccontextmanager
async def lifespan(app_instance: FastAPI):
    """Управление жизненным циклом"""
    # Инициализация
    app_instance.state.db_pool = await asyncpg.create_pool(...)

    try:
        yield
    finally:
        # Очистка
        await app_instance.state.db_pool.close()

app = FastAPI(
    title="Project Name",
    version="1.0.0",
    lifespan=lifespan
)

# Подключение роутеров
app.include_router(user_router)
app.include_router(resource_router)

@app.get("/health")
async def health_check():
    return {"status": "healthy"}
```

---

## 8. Общие правила и best practices

### 8.1 Зависимости между слоями

**Правило зависимостей** (Dependency Rule):

```
Presentation → Application → Domain
     ↓              ↓
Infrastructure  (зависит от Domain, но не наоборот)
```

- **Domain** не зависит ни от чего
- **Application** зависит только от **Domain**
- **Infrastructure** реализует интерфейсы **Domain**
- **Presentation** зависит от **Application** и **Domain**

### 8.2 Именование

| Элемент        | Стиль       | Пример                               |
| -------------- | ----------- | ------------------------------------ |
| Файлы          | snake_case  | `register_user.py`                   |
| Классы         | PascalCase  | `RegisterUser`                       |
| Функции/методы | snake_case  | `execute()`, `get_user_repository()` |
| Константы      | UPPER_CASE  | `MAX_USERS`                          |
| Приватные      | префикс `_` | `_convert_to_entity()`               |

### 8.3 Структура модулей

**Каждый пакет должен иметь**:

- `__init__.py` - экспорт публичного API
- Логическая группировка файлов по сущностям

**Пример `__init__.py`**:

```python
# domain/entities/__init__.py
from .user import User, SubscriptionStatus
from .post import Post
from .resource import Resource, ResourceType

__all__ = [
    "User",
    "SubscriptionStatus",
    "Post",
    "Resource",
    "ResourceType",
]
```

### 8.4 Обработка ошибок

**Поток обработки**:

1. **Domain** выбрасывает доменные исключения
2. **Application** пропускает их дальше или оборачивает
3. **Infrastructure** конвертирует технические ошибки в доменные
4. **Presentation** перехватывает и конвертирует в HTTP статусы

**Пример**:

```python
# Domain
raise UserNotFoundError(user_id="123")

# Presentation
except UserNotFoundError as e:
    raise HTTPException(status_code=404, detail=str(e))
```

### 8.5 Асинхронность

- Используйте `async/await` везде, где возможно
- Репозитории - асинхронные (`async def`)
- Use cases - асинхронные
- Endpoints - асинхронные

### 8.6 Типизация

- Используйте type hints везде
- `from typing import Optional, List, Tuple, Dict`
- `from uuid import UUID`
- `from datetime import datetime`

### 8.7 Документация

```python
def method(self, param: str) -> Result:
    """
    Краткое описание в одну строку.

    Args:
        param: описание параметра

    Returns:
        описание возвращаемого значения

    Raises:
        ExceptionType: когда выбрасывается
    """
```

---

## 9. Чеклист для рефакторинга

При рефакторинге старого кода проверьте:

### Domain

- [ ] Сущности содержат бизнес-логику
- [ ] Интерфейсы репозиториев не зависят от реализации
- [ ] Исключения описывают бизнес-проблемы
- [ ] Нет зависимостей от фреймворков

### Application

- [ ] Use cases оркестрируют, а не реализуют логику
- [ ] Один use case = одна операция
- [ ] DTO используются для входа/выхода
- [ ] Зависимости через конструктор (DI)

### Infrastructure

- [ ] Репозитории реализуют интерфейсы из Domain
- [ ] Конвертация данных изолирована (DB ↔ Domain)
- [ ] Технические ошибки конвертируются в доменные

### Presentation

- [ ] Endpoints только делегируют use cases
- [ ] Pydantic схемы для валидации
- [ ] Обработка исключений → HTTP статусы
- [ ] Dependencies для DI

### Общее

- [ ] Правило зависимостей соблюдено
- [ ] Типизация везде
- [ ] Асинхронный код
- [ ] Документация

---

## 10. Примеры распространенных ошибок

### ❌ Неправильно

```python
# Domain зависит от FastAPI
from fastapi import HTTPException
class User:
    def validate(self):
        if not self.email:
            raise HTTPException(status_code=400, detail="Invalid")

# Use case содержит SQL
class GetUser:
    async def execute(self, user_id):
        row = await db.fetchrow("SELECT * FROM users WHERE id = $1", user_id)
        return row

# Endpoint содержит бизнес-логику
@router.post("/register")
async def register(data: UserRegister):
    if len(data.password) < 8:
        raise HTTPException(400, "Weak password")
    hashed = hash_password(data.password)
    await db.execute("INSERT INTO users ...")
```

### ✅ Правильно

```python
# Domain - чистая бизнес-логика
class User:
    def validate(self):
        if not self.email:
            raise InvalidEmailError(self.email)

# Use case - оркестрация
class GetUser:
    def __init__(self, repository: UserRepository):
        self._repository = repository

    async def execute(self, request: GetUserRequest):
        user = await self._repository.get_by_id(request.user_id)
        if not user:
            raise UserNotFoundError(request.user_id)
        return UserResponseDTO(...)

# Endpoint - делегирование
@router.post("/register")
async def register(
    data: UserRegister,
    use_case: RegisterUser = Depends(get_register_user_use_case)
):
    try:
        request = RegisterUserRequest(...)
        response = await use_case.execute(request)
        return response
    except UserAlreadyExistsError as e:
        raise HTTPException(409, str(e))
```

---

## Заключение

Эта архитектура обеспечивает:

- ✅ **Тестируемость** - слои изолированы
- ✅ **Масштабируемость** - легко добавлять новые фичи
- ✅ **Гибкость** - легко менять БД, фреймворки
- ✅ **Поддерживаемость** - понятная структура
- ✅ **Независимость от фреймворков** - бизнес-логика изолирована

При рефакторинге следуйте этим правилам последовательно, начиная с Domain слоя.

