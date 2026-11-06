from typing import Annotated
from fastapi import FastAPI, Depends, HTTPException, Response
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from sqlmodel import Session, select

from database import engine, create_db_and_tables, get_session
from models import (
    Event, EventCreate, EventUpdate, EventPublic,
    Registration, RegistrationCreate, RegistrationPublic
)

create_db_and_tables()

app = FastAPI(title="Events DB", version="2.0")
SessionDep = Annotated[Session, Depends(get_session)]

# --- Обработчик ошибок ---
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request, exc):
    return JSONResponse(
        status_code=400,
        content={"detail": "Невалидные данные", "errors": exc.errors()}
    )

# --- Health ---
@app.get("/health")
def health():
    return {"status": "ok"}

# --- CRUD для Event ---

@app.post("/api/events", response_model=EventPublic, status_code=201)
def create_event(event: EventCreate, session: SessionDep):
    db_event = Event.model_validate(event)
    session.add(db_event)
    session.commit()
    session.refresh(db_event)
    return db_event

@app.get("/api/events", response_model=list[EventPublic])
def list_events(session: SessionDep, skip: int = 0, limit: int = 100):
    return session.exec(select(Event).offset(skip).limit(limit)).all()

@app.get("/api/events/{event_id}", response_model=EventPublic)
def get_event(event_id: int, session: SessionDep):
    event = session.get(Event, event_id)
    if not event:
        raise HTTPException(status_code=404, detail="Мероприятие не найдено")
    return event

@app.put("/api/events/{event_id}", response_model=EventPublic)
def update_event(event_id: int, event_update: EventCreate, session: SessionDep):
    event = session.get(Event, event_id)
    if not event:
        raise HTTPException(status_code=404, detail="Мероприятие не найдено")
    for key, value in event_update.model_dump().items():
        setattr(event, key, value)
    session.add(event)
    session.commit()
    session.refresh(event)
    return event

@app.patch("/api/events/{event_id}", response_model=EventPublic)
def patch_event(event_id: int, event_update: EventUpdate, session: SessionDep):
    event = session.get(Event, event_id)
    if not event:
        raise HTTPException(status_code=404, detail="Мероприятие не найдено")
    update_data = event_update.model_dump(exclude_unset=True)
    if not update_data:
        raise HTTPException(status_code=400, detail="Нужно хотя бы одно поле")
    for key, value in update_data.items():
        setattr(event, key, value)
    session.add(event)
    session.commit()
    session.refresh(event)
    return event

@app.delete("/api/events/{event_id}", status_code=204)
def delete_event(event_id: int, session: SessionDep):
    event = session.get(Event, event_id)
    if not event:
        raise HTTPException(status_code=404, detail="Мероприятие не найдено")
    session.delete(event)
    session.commit()
    return Response(status_code=204)

# --- Вложенные маршруты для Registration ---

@app.post(
    "/api/events/{event_id}/registrations",
    response_model=RegistrationPublic,
    status_code=201
)
def create_registration(
    event_id: int,
    registration: RegistrationCreate,
    session: SessionDep
):
    # 1. Проверяем, что мероприятие существует
    event = session.get(Event, event_id)
    if not event:
        raise HTTPException(status_code=404, detail="Мероприятие не найдено")
    
    # 2. Проверяем лимит участников
    count = session.exec(
        select(Registration).where(Registration.event_id == event_id)
    ).all()
    if len(count) >= event.capacity:
        raise HTTPException(status_code=409, detail="Лимит участников исчерпан")
    
    # 3. Проверяем уникальность email на это мероприятие
    existing = session.exec(
        select(Registration).where(
            Registration.event_id == event_id,
            Registration.email == registration.email
        )
    ).first()
    if existing:
        raise HTTPException(status_code=409, detail="Этот email уже зарегистрирован")
    
    # 4. ✅ ПРАВИЛЬНОЕ СОЗДАНИЕ: распаковываем данные и добавляем event_id
    db_registration = Registration(
        **registration.model_dump(),
        event_id=event_id
    )
    
    session.add(db_registration)
    session.commit()
    session.refresh(db_registration)
    return db_registration
@app.get(
    "/api/events/{event_id}/registrations",
    response_model=list[RegistrationPublic]
)
def list_registrations(event_id: int, session: SessionDep):
    # Проверяем, что мероприятие существует
    event = session.get(Event, event_id)
    if not event:
        raise HTTPException(status_code=404, detail="Мероприятие не найдено")
    
    # Возвращаем список регистраций
    return session.exec(
        select(Registration).where(Registration.event_id == event_id)
    ).all()