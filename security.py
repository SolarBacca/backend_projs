import os
from datetime import datetime, timedelta, timezone

import jwt  
import time
from collections import defaultdict, deque
import bcrypt


def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def verify_password(password: str, password_hash: str) -> bool:
    return bcrypt.checkpw(password.encode("utf-8"), password_hash.encode("utf-8"))


JWT_ALGORITHM = "HS256"


def create_access_token(user: "User") -> str: 
    secret = os.getenv("JWT_SECRET", "dev-secret")
    ttl = int(os.getenv("JWT_TTL_MINUTES", "30"))
    now = datetime.now(timezone.utc)
    payload = {
        "sub": str(user.id),        
        "username": user.username,
        "role": user.role,
        "iat": now,               
        "exp": now + timedelta(minutes=ttl),  
    }
    return jwt.encode(payload, secret, algorithm=JWT_ALGORITHM)


def decode_access_token(token: str) -> dict | None:
   
    try:
        return jwt.decode(token, os.getenv("JWT_SECRET", "dev-secret"),
                          algorithms=[JWT_ALGORITHM])
    except jwt.PyJWTError:
        return None


LOGIN_LIMIT = 5
LOGIN_WINDOW_SECONDS = 60
_login_failures: dict[str, deque[float]] = defaultdict(deque)


def _recent_failures(key: str) -> deque[float]:
    now = time.monotonic()
    dq = _login_failures[key]
    while dq and now - dq[0] > LOGIN_WINDOW_SECONDS:
        dq.popleft()         
    return dq


def note_login_failure(key: str) -> bool:
    
    dq = _recent_failures(key)
    dq.append(time.monotonic())
    return len(dq) >= LOGIN_LIMIT


def clear_login_failures(key: str) -> None:
 
    _login_failures.pop(key, None)