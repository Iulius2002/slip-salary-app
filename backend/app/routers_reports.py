from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.orm import Session
from sqlalchemy import select, func, and_
from datetime import date, timedelta
import calendar
import os, csv, decimal, glob, shutil
from datetime import datetime

from app.db import SessionLocal
from app.models import User, UserRole as ModelRole, WorkLog, Vacation, Bonus, Employment
from app.routers_auth import require_manager
from app.idempotency import with_idempotency
from app.emailer import send_email
from app.config import settings

router = APIRouter(tags=["reports"])

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def month_bounds(d: date):
    first = d.replace(day=1)
    last = d.replace(day=calendar.monthrange(d.year, d.month)[1])
    return first, last

def overlap_weekdays(start: date, end: date, month_start: date, month_end: date) -> int:
    # count weekdays in the overlap of [start,end] and [month_start,month_end]
    s = max(start, month_start)
    e = min(end, month_end)
    if s > e:
        return 0
    cur, days = s, 0
    while cur <= e:
        if cur.weekday() < 5:
            days += 1
        cur += timedelta(days=1)
    return days

@router.post("/createAggregatedEmployeeData")
@with_idempotency("createAggregatedEmployeeData")
def create_aggregated_employee_data(
    manager: User = Depends(require_manager),
    db: Session = Depends(get_db),
    request: Request = None,   # ensures the idempotency decorator can read headers
):
    """Generates a CSV for the current manager with current-month metrics."""
    today = date.today()
    month_start, month_end = month_bounds(today)

    employees = db.scalars(
        select(User)
        .where(and_(User.role == ModelRole.employee, User.manager_id == manager.id))
        .order_by(User.last_name, User.first_name)
    ).all()

    if not employees:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No employees for this manager")

    rows = []
    for emp in employees:
        employment = db.scalar(select(Employment).where(Employment.user_id == emp.id))
        base_salary = float(employment.base_salary) if employment and employment.base_salary is not None else 0.0

        workdays = db.scalar(
            select(func.count(WorkLog.id)).where(
                and_(
                    WorkLog.user_id == emp.id,
                    WorkLog.work_date >= month_start,
                    WorkLog.work_date <= month_end,
                )
            )
        ) or 0

        vacations = db.scalars(
            select(Vacation).where(Vacation.user_id == emp.id)
            .where(Vacation.end_date >= month_start)
            .where(Vacation.start_date <= month_end)
        ).all()
        vacation_days = sum(
            overlap_weekdays(v.start_date, v.end_date, month_start, month_end) for v in vacations
        )

        bonuses_sum_dec = db.scalar(
            select(func.coalesce(func.sum(Bonus.amount), 0)).where(
                and_(
                    Bonus.user_id == emp.id,
                    Bonus.bonus_date >= month_start,
                    Bonus.bonus_date <= month_end,
                )
            )
        ) or decimal.Decimal("0.00")
        bonuses_sum = float(bonuses_sum_dec)

        salary_to_pay = base_salary + bonuses_sum

        rows.append(
            {
                "Employee name": f"{emp.first_name} {emp.last_name}",
                "Salary to be paid for the current month": f"{salary_to_pay:.2f}",
                "Number of working days during the month": workdays,
                "Number of vacation days taken": vacation_days,
                "Additional bonuses (if any)": f"{bonuses_sum:.2f}",
            }
        )

    out_dir = os.path.join(os.path.dirname(__file__), "..", "storage", "csv")
    out_dir = os.path.abspath(out_dir)
    os.makedirs(out_dir, exist_ok=True)

    filename = f"aggregated_{manager.id}_{today.strftime('%Y%m')}.csv"
    out_path = os.path.join(out_dir, filename)

    fieldnames = [
        "Employee name",
        "Salary to be paid for the current month",
        "Number of working days during the month",
        "Number of vacation days taken",
        "Additional bonuses (if any)",
    ]
    with open(out_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

    return {
        "ok": True,
        "file": out_path,
        "employees": len(rows),
        "month": today.strftime("%Y-%m"),
    }

@router.post("/sendAggregatedEmployeeData")
@with_idempotency("sendAggregatedEmployeeData")
def send_aggregated_employee_data(
    manager: User = Depends(require_manager),
    db: Session = Depends(get_db),
    request: Request = None,
):
    """Emails the current-month CSV to the manager and archives it."""
    today = date.today()
    month_str = today.strftime('%Y%m')

    csv_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "storage", "csv"))
    os.makedirs(csv_dir, exist_ok=True)

    pattern = os.path.join(csv_dir, f"aggregated_{manager.id}_{month_str}.csv")
    matches = glob.glob(pattern)

    if matches:
        csv_path = matches[0]
    else:
        res = create_aggregated_employee_data(manager=manager, db=db, request=request)
        if not res.get("ok"):
            raise HTTPException(status_code=500, detail="Failed to create CSV")
        csv_path = res["file"]

    with open(csv_path, "rb") as f:
        csv_bytes = f.read()

    subject = f"Employee Aggregated Report - {today.strftime('%B %Y')}"
    sender = "noreply@slip-salary.local"
    recipients = [manager.email]
    body = f"Hello {manager.first_name},\n\nAttached is your team CSV for {today.strftime('%B %Y')}.\n\nRegards,\nSlip Salary App"

    send_email(
        smtp_host=settings.smtp_host,
        smtp_port=settings.smtp_port,
        subject=subject,
        sender=sender,
        recipients=recipients,
        body=body,
        attachments=[(os.path.basename(csv_path), csv_bytes, "text/csv")],
    )

    archive_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "storage", "archive", "csv"))
    os.makedirs(archive_dir, exist_ok=True)
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    archived_path = os.path.join(archive_dir, f"{os.path.basename(csv_path).removesuffix('.csv')}_{ts}.csv")
    shutil.copy2(csv_path, archived_path)

    return {
        "ok": True,
        "emailed_to": manager.email,
        "file_sent": csv_path,
        "archived_as": archived_path,
        "month": today.strftime("%Y-%m"),
    }
