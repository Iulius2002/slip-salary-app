from pydantic import BaseModel, EmailStr
from enum import Enum

class UserRole(str, Enum):
    manager = "manager"
    employee = "employee"

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"

class LoginRequest(BaseModel):
    email: EmailStr
    password: str

class UserOut(BaseModel):
    id: int
    email: EmailStr
    first_name: str
    last_name: str
    role: UserRole

    class Config:
        from_attributes = True
