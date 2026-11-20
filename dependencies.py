
import base64
from typing import Annotated

from fastapi import Depends, HTTPException, Request, status
from sqlmodel import Session, select

from database import get_session
from models import User, Event
from security import verify_password


def _unauthorized() -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Не авторизован",
        headers={"WWW-Authenticate": "Basic"},  
    )


def get_current_user(
    request: Request,
    session: Session = Depends(get_session),
) -> User:
    header = request.headers.get("Authorization", "")
    scheme, _, credentials = header.partition(" ")

  
    if scheme.lower() != "basic" or not credentials:
        raise _unauthorized()

   
    try:
        decoded = base64.b64decode(credentials, validate=True).decode("utf-8")
    except (ValueError, UnicodeDecodeError):
        raise _unauthorized()

    username, _, password = decoded.partition(":")
    if not username or not password:
        raise _unauthorized()

    user = session.exec(select(User).where(User.username == username)).first()
    if user is None or not verify_password(password, user.password_hash):
        raise _unauthorized()

    return user
  

CurrentUser = Annotated[User, Depends(get_current_user)]

def get_owned_event(
    event_id: int,
    session: Session = Depends(get_session),
    user: CurrentUser = None,        
) -> Event:
 
    event = session.get(Event, event_id)
    if not event:
        raise HTTPException(status_code=404, detail="Мероприятие не найдено")
    
    if user.role != "admin" and event.owner_id != user.id:
        raise HTTPException(status_code=403, detail="Это не ваше событие")
    return event


OwnedEvent = Annotated[Event, Depends(get_owned_event)]