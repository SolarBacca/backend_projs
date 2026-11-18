
import base64
from typing import Annotated

from fastapi import Depends, HTTPException, Request, status
from sqlmodel import Session, select

from database import get_session
from models import User
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

    # Заголовка нет или схема не Basic
    if scheme.lower() != "basic" or not credentials:
        raise _unauthorized()

    # Basic <base64(login:password)>
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