
import base64
from typing import Annotated

from fastapi import Depends, HTTPException, Request, status
from sqlmodel import Session, select

from database import get_session
from models import User, Event
from security import verify_password, decode_access_token, note_login_failure, clear_login_failures


def rate_limited() -> HTTPException:
    return HTTPException(
        status_code=429,
        detail="Слишком много неудачных попыток входа",
        headers={"Retry-After": "60"},
    )


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

    if scheme.lower() == "bearer":
        payload = decode_access_token(credentials)
        if payload is None:
            raise _unauthorized()          # подделка / просрочка → 401 без подсказок
        try:
            user = session.get(User, int(payload["sub"]))
        except (KeyError, ValueError, TypeError):
            raise _unauthorized()
        if user is None:
            raise _unauthorized()
        return user

  
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
    ok = user is not None and verify_password(password, user.password_hash)
    if not ok:
        if note_login_failure(username):   
            raise rate_limited()           
        raise _unauthorized()           
    clear_login_failures(username)         
    
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