from sqlmodel import SQLModel, Field, Relationship
from typing import Optional
from datetime import datetime, timezone
from pydantic import field_validator

# --- Event модели ---
class EventBase(SQLModel):
    title: str = Field(min_length=1)
    date: datetime  
    location: str = Field(min_length=1)
    capacity: int = Field(ge=1)

    @field_validator("date")
    @classmethod
    def ensure_tz(cls, v: datetime) -> datetime:
        if v.tzinfo is None:
            return v.replace(tzinfo=timezone.utc)
        return v


class Event(EventBase, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    # Связь один-ко-многим: у Event много Registration
    registrations: list["Registration"] = Relationship(
        back_populates="event", 
        cascade_delete=True
    )

class EventCreate(EventBase):
    pass

class EventUpdate(SQLModel):
    title: Optional[str] = None
    date: Optional[datetime] = None
    location: Optional[str] = None
    capacity: Optional[int] = None

class EventPublic(EventBase):
    id: int

# --- Registration модели ---
class RegistrationBase(SQLModel):
    name: str = Field(min_length=1)
    email: str = Field(min_length=1)

class Registration(RegistrationBase, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    event_id: int = Field(foreign_key="event.id")
    # Обратная связь
    event: Optional[Event] = Relationship(back_populates="registrations")

class RegistrationCreate(RegistrationBase):
    pass

class RegistrationPublic(RegistrationBase):
    id: int
    event_id: int


# User models
class UserBase(SQLModel):
    username: str = Field(min_length=1, max_length=50, index=True, unique=True)


class User(UserBase, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    password_hash: str                     
    role: str = Field(default="user")       

class UserCreate(SQLModel):
    """То, что присылает клиент. Поля role нет намерено."""
    username: str = Field(min_length=1, max_length=50)
    password: str = Field(min_length=1)     


class UserPublic(UserBase):
    """То, что возвращаем. Ни password, ни password_hash."""
    id: int