from typing import Generator
from fastapi import Depends, HTTPException, status
from sqlalchemy.orm import Session
from jose import JWTError, jwt

from app.db import SessionLocal
from app.config import settings
from app.models import User, UserRole

ALGORITHM = "HS256"

def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def get_current_user(token: str = Depends(lambda authorization: authorization),
                     db: Session = Depends(get_db)) -> User:
    # extract bearer token
    if token is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Missing Authorization header")
    if isinstance(token, str):
        # FastAPI trick: we depend on the whole header; read from request.state if needed.
        # Simpler: pull from starlette request headers
        # We'll override with a Request-dep below (see auth router). This function is kept token-centric.
        pass
    raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid dependency wiring")

# NOTE: We re-declare a proper version inside auth router using Request; keeping this placeholder so imports won't break.
