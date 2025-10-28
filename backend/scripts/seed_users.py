from sqlalchemy.orm import Session
from app.db import SessionLocal, engine, Base
from app.models import UserRole, Employment, User
from app.security import hash_password
from app.crud import create_user, get_user_by_email
from datetime import date

def ensure_user(db: Session, **kwargs):
    existing = get_user_by_email(db, kwargs["email"])
    if existing:
        return existing
    return create_user(db, **kwargs)

def main():
    db = SessionLocal()
    try:
        # Manager
        mgr = ensure_user(db,
            email="manager@example.com",
            password_hash=hash_password("Passw0rd!"),
            first_name="Mara",
            last_name="Manager",
            employee_code="MGR001",
            cnp="2990101012345",
            role=UserRole.manager,
            manager_id=None,
        )

        # Employees
        e1 = ensure_user(db,
            email="alice@example.com",
            password_hash=hash_password("Passw0rd!"),
            first_name="Alice",
            last_name="Ionescu",
            employee_code="EMP001",
            cnp="2980202123456",
            role=UserRole.employee,
            manager_id=mgr.id,
        )
        e2 = ensure_user(db,
            email="bob@example.com",
            password_hash=hash_password("Passw0rd!"),
            first_name="Bob",
            last_name="Popescu",
            employee_code="EMP002",
            cnp="1970303123456",
            role=UserRole.employee,
            manager_id=mgr.id,
        )

        # Minimal employment rows (so they exist later)
        for u, salary in [(e1, 7000), (e2, 7500), (mgr, 12000)]:
            if not u.employment:
                emp = Employment(
                    user_id=u.id,
                    hire_date=date(2023,1,1),
                    base_salary=salary
                )
                db.add(emp)
        db.commit()

        print("Seeded users. Manager login: manager@example.com / Passw0rd!")
        print("Employees: alice@example.com, bob@example.com / Passw0rd!")
    finally:
        db.close()

if __name__ == "__main__":
    main()
