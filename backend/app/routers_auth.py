from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.orm import Session
from jose import jwt, JWTError

from app.config import settings
from app.security import verify_password, create_access_token
from app.crud import get_user_by_email, get_user
from app.db import SessionLocal
from app.schemas import LoginRequest, TokenResponse, UserOut
from app.models import User, UserRole as ModelRole

ALGORITHM = "HS256"

router = APIRouter(prefix="/auth", tags=["auth"])

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def bearer_token_from_request(request: Request) -> str:
    auth = request.headers.get("Authorization")
    if not auth or not auth.lower().startswith("bearer "):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated")
    return auth.split(" ", 1)[1].strip()

def get_current_user(request: Request, db: Session = Depends(get_db)) -> User:
    token = bearer_token_from_request(request)
    try:
        # ✅ decode with the JWT secret from .env
        payload = jwt.decode(token, settings.jwt_secret, algorithms=[ALGORITHM])
    except JWTError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")

    user_id = payload.get("sub")
    if user_id is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token payload")

    user = get_user(db, int(user_id))
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found")
    return user

def require_manager(user: User = Depends(get_current_user)) -> User:
    if user.role != ModelRole.manager:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Managers only")
    return user

@router.post("/login", response_model=TokenResponse)
def login(data: LoginRequest, db: Session = Depends(get_db)):
    user = get_user_by_email(db, data.email)
    if not user or not verify_password(data.password, user.password_hash):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid email or password")

    token = create_access_token(
        data={"sub": str(user.id), "email": user.email, "role": user.role.value},
        secret=settings.jwt_secret,
        expires_minutes=int(settings.jwt_expire_minutes),
    )
    return TokenResponse(access_token=token)

@router.get("/me", response_model=UserOut)
def me(current_user: User = Depends(get_current_user)):
    return current_user

# Simple protected route for managers (to test role guard)
manager_router = APIRouter(prefix="/manager", tags=["manager"])

@manager_router.get("/ping")
def manager_ping(_: User = Depends(require_manager)):
    return {"ok": True, "who": "manager"}
