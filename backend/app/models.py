from datetime import date
from sqlalchemy import String, Integer, Date, ForeignKey, Numeric, Enum, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship
import enum

from app.db import Base

class UserRole(str, enum.Enum):
    manager = "manager"
    employee = "employee"

class Department(Base):
    __tablename__ = "departments"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)

    users: Mapped[list["User"]] = relationship(back_populates="department")

class User(Base):
    __tablename__ = "users"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False, default="")
    first_name: Mapped[str] = mapped_column(String(100), nullable=False)
    last_name: Mapped[str] = mapped_column(String(100), nullable=False)
    employee_code: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    cnp: Mapped[str] = mapped_column(String(20), unique=True, nullable=False)  # used later as PDF password
    role: Mapped[UserRole] = mapped_column(Enum(UserRole), nullable=False, default=UserRole.employee)

    manager_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"), nullable=True)
    manager: Mapped["User"] = relationship(remote_side=[id])

    department_id: Mapped[int | None] = mapped_column(ForeignKey("departments.id"))
    department: Mapped["Department"] = relationship(back_populates="users")

    employment: Mapped["Employment"] = relationship(back_populates="user", uselist=False, cascade="all, delete-orphan")
    vacations: Mapped[list["Vacation"]] = relationship(back_populates="user", cascade="all, delete-orphan")
    bonuses: Mapped[list["Bonus"]] = relationship(back_populates="user", cascade="all, delete-orphan")

class Employment(Base):
    __tablename__ = "employment"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), unique=True, nullable=False)
    hire_date: Mapped[date] = mapped_column(Date, nullable=False)
    end_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    base_salary: Mapped[float] = mapped_column(Numeric(12,2), nullable=False, default=0)

    user: Mapped["User"] = relationship(back_populates="employment")

class Vacation(Base):
    __tablename__ = "vacations"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    start_date: Mapped[date] = mapped_column(Date, nullable=False)
    end_date: Mapped[date] = mapped_column(Date, nullable=False)
    days: Mapped[int] = mapped_column(Integer, nullable=False)

    user: Mapped["User"] = relationship(back_populates="vacations")

    __table_args__ = (
        UniqueConstraint("user_id", "start_date", "end_date", name="uq_vacation_span"),
    )

class Bonus(Base):
    __tablename__ = "bonuses"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    bonus_date: Mapped[date] = mapped_column(Date, nullable=False)
    amount: Mapped[float] = mapped_column(Numeric(12,2), nullable=False)
    reason: Mapped[str] = mapped_column(String(255), nullable=True)

    user: Mapped["User"] = relationship(back_populates="bonuses")

class WorkLog(Base):
    __tablename__ = "work_logs"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    work_date: Mapped[date] = mapped_column(Date, nullable=False)
    hours: Mapped[float] = mapped_column(Numeric(4,2), nullable=False, default=8)
    note: Mapped[str | None] = mapped_column(String(255), nullable=True)

    user: Mapped["User"] = relationship()

    __table_args__ = (
        UniqueConstraint("user_id", "work_date", name="uq_worklog_user_date"),
    )

from sqlalchemy import JSON, DateTime
from datetime import datetime

class IdempotencyRecord(Base):
    __tablename__ = "idempotency_records"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    key: Mapped[str] = mapped_column(String(128), unique=True, nullable=False)
    endpoint: Mapped[str] = mapped_column(String(255), nullable=False)
    status_code: Mapped[int] = mapped_column(Integer, nullable=False)
    response_json: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=datetime.utcnow)
