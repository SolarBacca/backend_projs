from typing import Annotated
from fastapi import FastAPI, Depends, HTTPException, Response
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from sqlmodel import Session, select, col 

from database import engine, create_db_and_tables, get_session

from models import (
    Event, EventCreate, EventUpdate, EventPublic,
    Registration, RegistrationCreate, RegistrationPublic,
    User, UserCreate, UserPublic,          
)
from security import hash_password         
from dependencies import CurrentUser, OwnedEvent
 
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

# Auth (public endpoint)
@app.post("/auth/register", response_model=UserPublic, status_code=201)
def register(user_in: UserCreate, session: SessionDep):
    existing = session.exec(
        select(User).where(User.username == user_in.username)
    ).first()
    if existing:
        raise HTTPException(status_code=409, detail="Пользователь с таким логином уже существует")
    user = User(username=user_in.username, password_hash=hash_password(user_in.password))
    session.add(user)
    session.commit()
    session.refresh(user)
    return user

# --- CRUD для Event ---

@app.post("/api/events", response_model=EventPublic, status_code=201)
def create_event(event: EventCreate, session: SessionDep, user: CurrentUser):
    
    db_event = Event.model_validate(event)
    db_event.owner_id = user.id  
    session.add(db_event)
    session.commit()
    session.refresh(db_event)
    return db_event


@app.get("/api/events", response_model=list[EventPublic])
def list_events(session: SessionDep, q: str | None = None, skip: int = 0, limit: int = 100):
    stmt = select(Event)
    if q: 
        stmt = stmt.where(col(Event.title).ilike(f"%{q}%"))
    return session.exec(stmt.offset(skip).limit(limit)).all()


@app.get("/api/events/{event_id}", response_model=EventPublic)
def get_event(event_id: int, session: SessionDep):
    event = session.get(Event, event_id)
    if not event:
        raise HTTPException(status_code=404, detail="Мероприятие не найдено")
    return event

@app.put("/api/events/{event_id}", response_model=EventPublic)
def update_event(event: OwnedEvent, event_update: EventCreate, session: SessionDep):
    for key, value in event_update.model_dump().items():
        setattr(event, key, value)
    session.add(event)
    session.commit()
    session.refresh(event)
    return event

@app.patch("/api/events/{event_id}", response_model=EventPublic)
def patch_event(event: OwnedEvent, event_update: EventUpdate, session: SessionDep):
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
def delete_event(event: OwnedEvent, session: SessionDep) -> Response:
    session.delete(event)
    session.commit()
    return Response(status_code=204)

# --- Вложенные маршруты для Registration ---

@app.post("/api/events/{event_id}/registrations", response_model=RegistrationPublic, status_code=201)
def create_registration(event_id: int, registration: RegistrationCreate,
                        session: SessionDep, user: CurrentUser):
    
    
    event = session.get(Event, event_id)
    if not event:
        raise HTTPException(status_code=404, detail="Мероприятие не найдено")
    
    
    count = session.exec(
        select(Registration).where(Registration.event_id == event_id)
    ).all()
    if len(count) >= event.capacity:
        raise HTTPException(status_code=409, detail="Лимит участников исчерпан")
    
    
    existing = session.exec(
        select(Registration).where(
            Registration.event_id == event_id,
            Registration.email == registration.email
        )
    ).first()
    if existing:
        raise HTTPException(status_code=409, detail="Этот email уже зарегистрирован")
    
    
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
    event = session.get(Event, event_id)
    if not event:
        raise HTTPException(status_code=404, detail="Мероприятие не найдено")
    

    return session.exec(
        select(Registration).where(Registration.event_id == event_id)
    ).all()


# Auth
@app.post("/auth/register", response_model=UserPublic, status_code=201)
def register(user_in: UserCreate, session: SessionDep):
    existing = session.exec(
        select(User).where(User.username == user_in.username)
    ).first()
    if existing:
        raise HTTPException(status_code=409, detail="Пользователь с таким логином уже существует")
    user = User(username=user_in.username, password_hash=hash_password(user_in.password))
    session.add(user)
    session.commit()
    session.refresh(user)
    return user


@app.get("/auth/login", response_model=UserPublic)
def login(user: CurrentUser):
    return user


@app.get("/auth/me", response_model=UserPublic)
def me(user: CurrentUser):
    return user