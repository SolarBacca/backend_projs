from fastapi import FastAPI, HTTPException, Response
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from typing import Optional


app = FastAPI()


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request, exc):
    return JSONResponse(
        status_code=400,
        content={"detail": "Невалидные данные", "errors": exc.errors()}
    )


db: dict[int, dict] = {}
next_id = 1


class EventIn(BaseModel):
    title: str = Field(..., min_length=1)  
    date: str
    location: str = Field(..., min_length=1) 
    capacity: int = Field(..., ge=1)

class Event(EventIn):
    id: int

class EventPatch(BaseModel):
    title: Optional[str] = Field(None, min_length=1)
    date: Optional[str] = None
    location: Optional[str] = Field(None, min_length=1)
    capacity: Optional[int] = Field(None, ge=1)

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

@app.get("/api/events")
def list_events():
    return list(db.values())


@app.get("/api/events/{event_id}")
def get_event(event_id: int):
    if event_id not in db:
        raise HTTPException(status_code=404, detail="Мероприятие не найдено")
    return db[event_id]


@app.put("/api/events/{event_id}")
def update_event(event_id: int, payload: EventIn):
    if event_id not in db:
        raise HTTPException(status_code=404, detail="Мероприятие не найдено")
    
    updated = Event(id=event_id, **payload.model_dump())
    db[event_id] = updated
    return updated


@app.patch("/api/events/{event_id}")
def patch_event(event_id: int, payload: EventPatch):
    if event_id not in db:
        raise HTTPException(status_code=404, detail="Мероприятие не найдено")
    
    changes = payload.model_dump(exclude_unset=True)
    if not changes:
        raise HTTPException(status_code=400, detail="Нужно хотя бы одно поле для обновления")
 
    current = db[event_id]
    updated = current.model_copy(update=changes)
    db[event_id] = updated
    return updated


@app.delete("/api/events/{event_id}", status_code=204)
def delete_event(event_id: int):
    if event_id not in db:
        raise HTTPException(status_code=404, detail="Мероприятие не найдено")
    del db[event_id]
    return Response(status_code=204)