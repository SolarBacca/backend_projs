from fastapi import FastAPI
from pydantic import BaseModel


app = FastAPI()

db: dict[int, dict] = {}
next_id = 1


class EventIn(BaseModel):
    title: str 
    date: str
    location: str
    capacity: int 

class Event(EventIn):
    id: int




@app.get("/health")
def read_root():
    return {"status": "ok"}


@app.post("/api/events", status_code=201)
def create_event(payload: EventIn):
    global next_id
    event = Event(id=next_id, **payload.model_dump())
    db[next_id] = event
    next_id += 1
    return event


@app.get("/items/{item_id}")
def read_item(item_id: int, q: str | None = None):
    return {"item_id": item_id, "q": q}