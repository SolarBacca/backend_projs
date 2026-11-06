# Лаба 1. HTTP CRUD в памяти

## Тема
Афиша мероприятий (Events). Данные хранятся в памяти программы.

## Поля сущности Event
- `id` (int) — серверный идентификатор
- `title` (str) — название мероприятия (обязательное)
- `date` (datetime) — дата и время проведения
- `location` (str) — место проведения (обязательное)
- `capacity` (int) — лимит участников

## Запуск
Предварительно требуется установка uv
https://docs.astral.sh/uv/getting-started/installation/


```bash
uv sync
uv run fastapi dev

```
## Эндпоинты

| Метод  | Путь                  | Описание             | Коды ответа   |
|--------|-----------------------|----------------------|---------------|
| GET    | `/health`             | Проверка здоровья    | 200           |
| POST   | `/api/events`         | Создать мероприятие  | 201, 400      |
| GET    | `/api/events`         | Список мероприятий   | 200           |
| GET    | `/api/events/{id}`    | Получить по ID       | 200, 404      |
| PUT    | `/api/events/{id}`    | Полная замена        | 200, 400, 404 |
| PATCH  | `/api/events/{id}`    | Частичное обновление | 200, 400, 404 |
| DELETE | `/api/events/{id}`    | Удалить мероприятие  | 204, 404      |


## ER-диаграмма

Связь между таблицами **1:N** (одно мероприятие может иметь много регистраций).

```mermaid
erDiagram
    EVENT ||--o{ REGISTRATION : "has registrations"
    EVENT {
        int id PK
        string title
        string date
        string location
        int capacity
    }
    REGISTRATION {
        int id PK
        string name
        string email
        int event_id FK
    }