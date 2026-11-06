from sqlmodel import SQLModel, Field, Relationship
from typing import Optional

# --- Event модели ---
class EventBase(SQLModel):
    title: str = Field(min_length=1)
    date: str
    location: str = Field(min_length=1)
    capacity: int = Field(ge=1)

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
    date: Optional[str] = None
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