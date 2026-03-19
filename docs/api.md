1. Принципы API

API должно быть:
	•	ресурсно-ориентированным;
	•	версионируемым;
	•	идемпотентным там, где это ожидается;
	•	единообразным по форматам ошибок, пагинации и фильтрации;
	•	безопасным по умолчанию.

Базовый префикс API:

/api/v1

Формат обмена:
	•	application/json для большинства операций;
	•	multipart/form-data для загрузки файлов.

Аутентификация:
	•	Authorization: Bearer <JWT> для всех защищенных методов.

⸻

2. Общие правила контрактов

2.1. Идентификаторы

Все основные сущности должны иметь стабильные внешние идентификаторы:
	•	id: string в формате UUID.

2.2. Временные поля

Все временные метки должны передаваться в ISO 8601 UTC:

"created_at": "2026-03-19T10:15:30Z"

2.3. Пагинация

Для коллекций использовать cursor-based пагинацию.

Пример:

{
  "items": [],
  "page": {
    "next_cursor": "eyJpZCI6ICJhYmMifQ==",
    "has_more": true
  }
}

Параметры запроса:
	•	limit
	•	cursor

2.4. Сортировка

Поддерживаемый параметр:
	•	sort

Пример:

?sort=-created_at

2.5. Ошибки

Единый формат ошибок:

{
  "error": {
    "code": "workspace_forbidden",
    "message": "Access to workspace is denied",
    "details": null,
    "request_id": "b3d6c1b4-2d4f-4b08-9f4d-1fd8c6a4a2b1"
  }
}

Минимальный набор кодов:
	•	unauthorized
	•	forbidden
	•	not_found
	•	validation_error
	•	conflict
	•	unsupported_media_type
	•	rate_limited
	•	internal_error

2.6. Частичное обновление

Для частичного обновления использовать PATCH.

2.7. Идемпотентность

Для небезопасных операций создания, критичных к повторам, поддерживать заголовок:
	•	Idempotency-Key

⸻

3. Ресурсная модель

Основные ресурсы:
	•	users
	•	auth
	•	workspaces
	•	workspace-members
	•	workspace-prompt
	•	workspace-documents
	•	chats
	•	messages

Связи:
	•	воркспейс содержит участников, системный промпт и документы;
	•	чат принадлежит одному пользователю и одному воркспейсу;
	•	сообщения принадлежат одному чату;
	•	чат является личным контекстом пользователя и не шарится между участниками воркспейса.  ￼

⸻

4. Auth API

4.1. Вход

POST /api/v1/auth/login

Request

{
  "email": "user@example.com",
  "password": "secret"
}

Response 200

{
  "access_token": "<jwt>",
  "refresh_token": "<refresh-token>",
  "token_type": "Bearer",
  "expires_in": 3600,
  "user": {
    "id": "2f3c5a89-4d55-4c34-98d8-95dbe6c50c31",
    "email": "user@example.com",
    "display_name": "Ivan Petrov"
  }
}

4.2. Обновление токена

POST /api/v1/auth/refresh

Request

{
  "refresh_token": "<refresh-token>"
}

Response 200

{
  "access_token": "<jwt>",
  "refresh_token": "<refresh-token>",
  "token_type": "Bearer",
  "expires_in": 3600
}

4.3. Завершение сессии

POST /api/v1/auth/logout

Request

{
  "refresh_token": "<refresh-token>"
}

Response 204

4.4. Текущий пользователь

GET /api/v1/auth/me

Response 200

{
  "id": "2f3c5a89-4d55-4c34-98d8-95dbe6c50c31",
  "email": "user@example.com",
  "display_name": "Ivan Petrov"
}


⸻

5. Workspace API

Воркспейс — корневой доменный ресурс. Он бывает private или shared; в нем живут документы и системный промпт, а пользователь внутри него ведет личные чаты.

5.1. Модель ресурса

{
  "id": "06cf3b57-6707-4834-bd43-7c120e08f4e4",
  "name": "Cardiology",
  "description": "Scientific workspace for cardiology materials",
  "type": "private",
  "access_mode": "owner_only",
  "my_role": "admin",
  "created_at": "2026-03-19T10:15:30Z",
  "updated_at": "2026-03-19T10:15:30Z"
}

Где:
	•	type: private | shared
	•	access_mode: owner_only | by_membership | global

5.2. Список доступных воркспейсов

GET /api/v1/workspaces

Query params
	•	type
	•	limit
	•	cursor
	•	sort

Response 200

{
  "items": [
    {
      "id": "06cf3b57-6707-4834-bd43-7c120e08f4e4",
      "name": "Cardiology",
      "description": "Scientific workspace for cardiology materials",
      "type": "private",
      "access_mode": "owner_only",
      "my_role": "admin",
      "created_at": "2026-03-19T10:15:30Z",
      "updated_at": "2026-03-19T10:15:30Z"
    }
  ],
  "page": {
    "next_cursor": null,
    "has_more": false
  }
}

5.3. Создание воркспейса

POST /api/v1/workspaces

Request

{
  "name": "Graph Retrieval",
  "description": "Workspace for graph-guided retrieval experiments",
  "type": "shared",
  "access_mode": "by_membership"
}

Response 201

{
  "id": "ab1f8d19-a1b8-4fe7-a761-0a3f9fd7e7f2",
  "name": "Graph Retrieval",
  "description": "Workspace for graph-guided retrieval experiments",
  "type": "shared",
  "access_mode": "by_membership",
  "my_role": "admin",
  "created_at": "2026-03-19T10:15:30Z",
  "updated_at": "2026-03-19T10:15:30Z"
}

5.4. Получение воркспейса

GET /api/v1/workspaces/{workspace_id}

5.5. Обновление воркспейса

PATCH /api/v1/workspaces/{workspace_id}

Request

{
  "name": "Graph Retrieval Lab",
  "description": "Updated description"
}

5.6. Удаление воркспейса

DELETE /api/v1/workspaces/{workspace_id}

Response 204

⸻

6. Workspace Members API

Участники имеют смысл только в shared воркспейсах.

6.1. Модель участника

{
  "user_id": "2f3c5a89-4d55-4c34-98d8-95dbe6c50c31",
  "email": "user@example.com",
  "display_name": "Ivan Petrov",
  "role": "admin",
  "joined_at": "2026-03-19T10:15:30Z"
}

6.2. Список участников

GET /api/v1/workspaces/{workspace_id}/members

Response 200

{
  "items": [
    {
      "user_id": "2f3c5a89-4d55-4c34-98d8-95dbe6c50c31",
      "email": "user@example.com",
      "display_name": "Ivan Petrov",
      "role": "admin",
      "joined_at": "2026-03-19T10:15:30Z"
    }
  ]
}

6.3. Добавление участника

POST /api/v1/workspaces/{workspace_id}/members

Request

{
  "user_id": "9b41e2d1-0c4b-40db-b80b-6bba9e6cd18e",
  "role": "user"
}

Response 201

{
  "user_id": "9b41e2d1-0c4b-40db-b80b-6bba9e6cd18e",
  "role": "user",
  "joined_at": "2026-03-19T10:15:30Z"
}

6.4. Изменение роли участника

PATCH /api/v1/workspaces/{workspace_id}/members/{user_id}

Request

{
  "role": "admin"
}

6.5. Удаление участника

DELETE /api/v1/workspaces/{workspace_id}/members/{user_id}

Response 204

Бизнес-ограничения:
	•	нельзя удалить последнего администратора;
	•	нельзя управлять участниками приватного воркспейса.

⸻

7. Workspace Prompt API

Системный промпт — singleton-ресурс воркспейса; изменяется только администратором и применяется ко всем запросам в рамках воркспейса.  ￼

7.1. Модель промпта

{
  "workspace_id": "06cf3b57-6707-4834-bd43-7c120e08f4e4",
  "content": "You are a scientific assistant specialized in cardiology.",
  "updated_at": "2026-03-19T10:15:30Z",
  "updated_by": "2f3c5a89-4d55-4c34-98d8-95dbe6c50c31"
}

7.2. Получение промпта

GET /api/v1/workspaces/{workspace_id}/prompt

7.3. Обновление промпта

PUT /api/v1/workspaces/{workspace_id}/prompt

Request

{
  "content": "You are a scientific assistant specialized in graph-guided retrieval."
}

Response 200

{
  "workspace_id": "06cf3b57-6707-4834-bd43-7c120e08f4e4",
  "content": "You are a scientific assistant specialized in graph-guided retrieval.",
  "updated_at": "2026-03-19T10:15:30Z",
  "updated_by": "2f3c5a89-4d55-4c34-98d8-95dbe6c50c31"
}


⸻

8. Workspace Documents API

Документы — ресурс воркспейса, используемый как база знаний для retrieval pipeline. Это согласуется с целевой архитектурой: файлы хранятся отдельно, эмбеддинги и графовая модель строятся поверх корпуса.

8.1. Модель документа

{
  "id": "d86f4fc7-6a6f-40a0-ae97-3df5c647d0d9",
  "workspace_id": "06cf3b57-6707-4834-bd43-7c120e08f4e4",
  "filename": "paper.pdf",
  "content_type": "application/pdf",
  "size_bytes": 2481901,
  "status": "processed",
  "created_at": "2026-03-19T10:15:30Z",
  "uploaded_by": "2f3c5a89-4d55-4c34-98d8-95dbe6c50c31"
}

Где status:
	•	uploaded
	•	processing
	•	processed
	•	failed

8.2. Список документов воркспейса

GET /api/v1/workspaces/{workspace_id}/documents

Response 200

{
  "items": [
    {
      "id": "d86f4fc7-6a6f-40a0-ae97-3df5c647d0d9",
      "workspace_id": "06cf3b57-6707-4834-bd43-7c120e08f4e4",
      "filename": "paper.pdf",
      "content_type": "application/pdf",
      "size_bytes": 2481901,
      "status": "processed",
      "created_at": "2026-03-19T10:15:30Z",
      "uploaded_by": "2f3c5a89-4d55-4c34-98d8-95dbe6c50c31"
    }
  ],
  "page": {
    "next_cursor": null,
    "has_more": false
  }
}

8.3. Загрузка документа

POST /api/v1/workspaces/{workspace_id}/documents
Content-Type: multipart/form-data

Form fields
	•	file
	•	title опционально

Response 201

{
  "id": "d86f4fc7-6a6f-40a0-ae97-3df5c647d0d9",
  "workspace_id": "06cf3b57-6707-4834-bd43-7c120e08f4e4",
  "filename": "paper.pdf",
  "content_type": "application/pdf",
  "size_bytes": 2481901,
  "status": "uploaded",
  "created_at": "2026-03-19T10:15:30Z",
  "uploaded_by": "2f3c5a89-4d55-4c34-98d8-95dbe6c50c31"
}

8.4. Получение документа

GET /api/v1/workspaces/{workspace_id}/documents/{document_id}

8.5. Удаление документа

DELETE /api/v1/workspaces/{workspace_id}/documents/{document_id}

Response 204

8.6. Статус обработки документа

GET /api/v1/workspaces/{workspace_id}/documents/{document_id}/processing

Response 200

{
  "document_id": "d86f4fc7-6a6f-40a0-ae97-3df5c647d0d9",
  "status": "processing",
  "stage": "embedding",
  "updated_at": "2026-03-19T10:15:30Z",
  "error": null
}

Опциональные stage:
	•	uploaded
	•	text_extraction
	•	chunking
	•	embedding
	•	graph_update
	•	completed

⸻

9. Chats API

Чат — личный ресурс пользователя внутри воркспейса. Он не является коллективным и служит только контейнером контекста и истории.  ￼

9.1. Модель чата

{
  "id": "0ee04eaf-8a5a-4c1f-857e-0ef8f48d31b4",
  "workspace_id": "06cf3b57-6707-4834-bd43-7c120e08f4e4",
  "title": "New chat",
  "created_at": "2026-03-19T10:15:30Z",
  "updated_at": "2026-03-19T10:16:10Z",
  "last_message_at": "2026-03-19T10:16:10Z"
}

Поле owner_id во внешнем контракте можно не возвращать, так как владелец всегда текущий пользователь.

9.2. Список моих чатов в воркспейсе

GET /api/v1/workspaces/{workspace_id}/chats

Query params
	•	limit
	•	cursor
	•	sort

Response 200

{
  "items": [
    {
      "id": "0ee04eaf-8a5a-4c1f-857e-0ef8f48d31b4",
      "workspace_id": "06cf3b57-6707-4834-bd43-7c120e08f4e4",
      "title": "Methods discussion",
      "created_at": "2026-03-19T10:15:30Z",
      "updated_at": "2026-03-19T10:16:10Z",
      "last_message_at": "2026-03-19T10:16:10Z"
    }
  ],
  "page": {
    "next_cursor": null,
    "has_more": false
  }
}

9.3. Создание чата

POST /api/v1/workspaces/{workspace_id}/chats

Request

{
  "title": "Methods discussion"
}

Response 201

{
  "id": "0ee04eaf-8a5a-4c1f-857e-0ef8f48d31b4",
  "workspace_id": "06cf3b57-6707-4834-bd43-7c120e08f4e4",
  "title": "Methods discussion",
  "created_at": "2026-03-19T10:15:30Z",
  "updated_at": "2026-03-19T10:15:30Z",
  "last_message_at": null
}

9.4. Получение чата

GET /api/v1/workspaces/{workspace_id}/chats/{chat_id}

9.5. Обновление чата

PATCH /api/v1/workspaces/{workspace_id}/chats/{chat_id}

Request

{
  "title": "Graph methods discussion"
}

9.6. Удаление чата

DELETE /api/v1/workspaces/{workspace_id}/chats/{chat_id}

Response 204

⸻

10. Messages API

Сообщения — дочерний ресурс чата. История сообщений хранится и доступна только владельцу чата.  ￼

10.1. Модель сообщения

{
  "id": "4b4f87ef-7c16-4617-88f2-7f9448aa2c0d",
  "chat_id": "0ee04eaf-8a5a-4c1f-857e-0ef8f48d31b4",
  "role": "user",
  "content": "Explain graph-guided retrieval.",
  "status": "completed",
  "created_at": "2026-03-19T10:16:10Z"
}

Где:
	•	role: user | assistant | system
	•	status: pending | completed | failed

10.2. История сообщений

GET /api/v1/workspaces/{workspace_id}/chats/{chat_id}/messages

Response 200

{
  "items": [
    {
      "id": "4b4f87ef-7c16-4617-88f2-7f9448aa2c0d",
      "chat_id": "0ee04eaf-8a5a-4c1f-857e-0ef8f48d31b4",
      "role": "user",
      "content": "Explain graph-guided retrieval.",
      "status": "completed",
      "created_at": "2026-03-19T10:16:10Z"
    },
    {
      "id": "9d2df75e-4cb9-452d-8576-9c3ba104d49e",
      "chat_id": "0ee04eaf-8a5a-4c1f-857e-0ef8f48d31b4",
      "role": "assistant",
      "content": "Graph-guided retrieval combines semantic similarity with structural signals from a concept graph.",
      "status": "completed",
      "created_at": "2026-03-19T10:16:12Z"
    }
  ],
  "page": {
    "next_cursor": null,
    "has_more": false
  }
}

10.3. Отправка сообщения

Рекомендуемый контракт — одна команда на пользовательское сообщение и генерацию ответа.

POST /api/v1/workspaces/{workspace_id}/chats/{chat_id}/messages

Request

{
  "content": "Explain graph-guided retrieval."
}

Response 201

{
  "user_message": {
    "id": "4b4f87ef-7c16-4617-88f2-7f9448aa2c0d",
    "chat_id": "0ee04eaf-8a5a-4c1f-857e-0ef8f48d31b4",
    "role": "user",
    "content": "Explain graph-guided retrieval.",
    "status": "completed",
    "created_at": "2026-03-19T10:16:10Z"
  },
  "assistant_message": {
    "id": "9d2df75e-4cb9-452d-8576-9c3ba104d49e",
    "chat_id": "0ee04eaf-8a5a-4c1f-857e-0ef8f48d31b4",
    "role": "assistant",
    "content": "Graph-guided retrieval combines semantic similarity with structural signals from a concept graph.",
    "status": "completed",
    "created_at": "2026-03-19T10:16:12Z"
  },
  "context": {
    "documents_used": [
      {
        "document_id": "d86f4fc7-6a6f-40a0-ae97-3df5c647d0d9",
        "filename": "paper.pdf"
      }
    ]
  }
}

Это лучший базовый контракт для зрелого API, потому что он:
	•	атомарен с точки зрения клиента;
	•	возвращает уже сохраненные сущности;
	•	допускает последующее расширение метаданными retrieval.

10.4. Асинхронная обработка

Если генерация выполняется асинхронно через фоновые задачи, допустим второй вариант ответа:

Response 202

{
  "user_message": {
    "id": "4b4f87ef-7c16-4617-88f2-7f9448aa2c0d",
    "chat_id": "0ee04eaf-8a5a-4c1f-857e-0ef8f48d31b4",
    "role": "user",
    "content": "Explain graph-guided retrieval.",
    "status": "completed",
    "created_at": "2026-03-19T10:16:10Z"
  },
  "assistant_message": {
    "id": "9d2df75e-4cb9-452d-8576-9c3ba104d49e",
    "chat_id": "0ee04eaf-8a5a-4c1f-857e-0ef8f48d31b4",
    "role": "assistant",
    "content": "",
    "status": "pending",
    "created_at": "2026-03-19T10:16:10Z"
  }
}

Тогда клиент дочитывает историю сообщений повторным GET.

⸻

11. Контракт прав доступа

11.1. Роли

Поддерживаются:
	•	admin
	•	user

11.2. Матрица прав

Workspace admin

Может:
	•	читать и изменять воркспейс;
	•	читать и изменять системный промпт;
	•	загружать и удалять документы;
	•	управлять участниками общего воркспейса;
	•	вести свои личные чаты.

Workspace user

Может:
	•	читать доступный воркспейс;
	•	читать системный промпт, если это разрешено UI/политикой;
	•	вести свои личные чаты;
	•	читать только свои чаты и свои сообщения;
	•	не может управлять документами, участниками и промптом.

⸻

12. Статусы и enum-значения

Для контракта лучше сразу зафиксировать закрытый набор enum.

Workspace
	•	type: private | shared
	•	access_mode: owner_only | by_membership | global

Member
	•	role: admin | user

Document
	•	status: uploaded | processing | processed | failed

Message
	•	role: user | assistant | system
	•	status: pending | completed | failed

⸻

13. HTTP-коды

Минимально используемые:
	•	200 OK — успешное чтение/обновление;
	•	201 Created — успешное создание;
	•	202 Accepted — принято в асинхронную обработку;
	•	204 No Content — успешное удаление;
	•	400 Bad Request — некорректный запрос;
	•	401 Unauthorized — отсутствует или невалиден JWT;
	•	403 Forbidden — нет прав;
	•	404 Not Found — ресурс не найден или недоступен;
	•	409 Conflict — конфликт состояния;
	•	415 Unsupported Media Type — неподдерживаемый тип файла;
	•	422 Unprocessable Entity — ошибка валидации;
	•	429 Too Many Requests — превышение лимита;
	•	500 Internal Server Error.

⸻

14. Минимальные правила валидации

Workspace
	•	name: 1..255 символов
	•	description: nullable, до 4000 символов

Prompt
	•	content: 1..20000 символов

Chat
	•	title: 1..255 символов, может быть автосгенерирован

Message
	•	content: 1..20000 символов

Document
	•	ограничение по типу и размеру файла задается конфигурацией системы

⸻

15. Что важно зафиксировать в OpenAPI

Чтобы зрелость API была действительно высокой, в спецификации надо явно описать:
	•	все схемы запросов и ответов;
	•	enum-значения;
	•	примеры payload;
	•	коды ошибок по каждому методу;
	•	security scheme для Bearer JWT;
	•	теги по доменам:
	•	Auth
	•	Workspaces
	•	Workspace Members
	•	Workspace Prompt
	•	Workspace Documents
	•	Chats
	•	Messages

⸻

16. Рекомендуемый набор endpoint’ов

Итоговый минимальный набор:

POST   /api/v1/auth/login
POST   /api/v1/auth/refresh
POST   /api/v1/auth/logout
GET    /api/v1/auth/me

GET    /api/v1/workspaces
POST   /api/v1/workspaces
GET    /api/v1/workspaces/{workspace_id}
PATCH  /api/v1/workspaces/{workspace_id}
DELETE /api/v1/workspaces/{workspace_id}

GET    /api/v1/workspaces/{workspace_id}/members
POST   /api/v1/workspaces/{workspace_id}/members
PATCH  /api/v1/workspaces/{workspace_id}/members/{user_id}
DELETE /api/v1/workspaces/{workspace_id}/members/{user_id}

GET    /api/v1/workspaces/{workspace_id}/prompt
PUT    /api/v1/workspaces/{workspace_id}/prompt

GET    /api/v1/workspaces/{workspace_id}/documents
POST   /api/v1/workspaces/{workspace_id}/documents
GET    /api/v1/workspaces/{workspace_id}/documents/{document_id}
DELETE /api/v1/workspaces/{workspace_id}/documents/{document_id}
GET    /api/v1/workspaces/{workspace_id}/documents/{document_id}/processing

GET    /api/v1/workspaces/{workspace_id}/chats
POST   /api/v1/workspaces/{workspace_id}/chats
GET    /api/v1/workspaces/{workspace_id}/chats/{chat_id}
PATCH  /api/v1/workspaces/{workspace_id}/chats/{chat_id}
DELETE /api/v1/workspaces/{workspace_id}/chats/{chat_id}

GET    /api/v1/workspaces/{workspace_id}/chats/{chat_id}/messages
POST   /api/v1/workspaces/{workspace_id}/chats/{chat_id}/messages


⸻

17. Архитектурное замечание

Для вашего стека это хорошо ложится на доменное разделение:
	•	auth
	•	identity
	•	workspaces
	•	documents
	•	chats
	•	messaging
	•	retrieval

А обработка документов и генерация ответа естественно уходят в фоновые пайплайны через Redis/Celery, при этом публичный API остается синхронным по форме и предсказуемым по контракту. Это согласуется с выбранным технологическим стеком и retrieval-подходом проекта.
