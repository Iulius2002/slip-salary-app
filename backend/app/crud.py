from sqlalchemy.orm import Session
from sqlalchemy import select
from app.models import User, UserRole

def get_user_by_email(db: Session, email: str) -> User | None:
    return db.scalar(select(User).where(User.email == email))

def get_user(db: Session, user_id: int) -> User | None:
    return db.get(User, user_id)

def create_user(db: Session, *, email: str, password_hash: str,
                first_name: str, last_name: str, employee_code: str,
                cnp: str, role: UserRole, manager_id: int | None = None):
    u = User(
        email=email,
        password_hash=password_hash,
        first_name=first_name,
        last_name=last_name,
        employee_code=employee_code,
        cnp=cnp,
        role=role,
        manager_id=manager_id,
    )
    db.add(u)
    db.commit()
    db.refresh(u)
    return u
