from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session
from sqlalchemy import select, func, and_
from datetime import date
import calendar, os, io, decimal, shutil

from pypdf import PdfReader, PdfWriter
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm

from app.db import SessionLocal
from app.models import User, UserRole as ModelRole, Employment, Bonus, Vacation, WorkLog
from app.routers_auth import require_manager
from app.emailer import send_email
from app.config import settings
from app.idempotency import with_idempotency

router = APIRouter(tags=["pdfs"])


# ---------- DB session helper ----------
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# ---------- Utility functions ----------
def month_bounds(d: date):
    first = d.replace(day=1)
    last = d.replace(day=calendar.monthrange(d.year, d.month)[1])
    return first, last


def count_vacation_days(db: Session, user_id: int, month_start: date, month_end: date) -> int:
    """Count vacation days within the month."""
    return (
        db.scalar(
            select(func.coalesce(func.sum(Vacation.days), 0))
            .where(and_(
                Vacation.user_id == user_id,
                Vacation.start_date >= month_start,
                Vacation.end_date <= month_end
            ))
        ) or 0
    )


def count_working_days(db: Session, user_id: int, month_start: date, month_end: date) -> int:
    """Count work log entries in the given month."""
    return (
        db.scalar(
            select(func.count(WorkLog.id))
            .where(and_(
                WorkLog.user_id == user_id,
                WorkLog.work_date >= month_start,
                WorkLog.work_date <= month_end
            ))
        ) or 0
    )


def calc_bonus_total(db: Session, user_id: int, month_start: date, month_end: date) -> float:
    """Sum all bonuses for user in the month."""
    bonuses_sum_dec = db.scalar(
        select(func.coalesce(func.sum(Bonus.amount), 0)).where(
            and_(
                Bonus.user_id == user_id,
                Bonus.bonus_date >= month_start,
                Bonus.bonus_date <= month_end
            )
        )
    ) or decimal.Decimal("0.00")
    return float(bonuses_sum_dec)


def calc_current_month_salary(db: Session, user_id: int, month_start: date, month_end: date) -> dict:
    """Return full salary breakdown for the current month."""
    emp = db.scalar(select(Employment).where(Employment.user_id == user_id))
    base = float(emp.base_salary) if emp and emp.base_salary is not None else 0.0
    bonuses = calc_bonus_total(db, user_id, month_start, month_end)
    vac_days = count_vacation_days(db, user_id, month_start, month_end)
    work_days = count_working_days(db, user_id, month_start, month_end)
    total = round(base + bonuses, 2)
    return {
        "base_salary": base,
        "bonus_total": bonuses,
        "vacation_days": vac_days,
        "working_days": work_days,
        "total_salary": total,
    }


# ---------- PDF generation ----------
def gen_pdf_bytes(
    *,
    full_name: str,
    employee_code: str,
    cnp: str,
    month_label: str,
    base_salary: float,
    working_days: int,
    vacation_days: int,
    bonus_total: float,
    total_salary: float
) -> bytes:
    """Generate a password-protected salary slip PDF."""
    buf = io.BytesIO()
    c = canvas.Canvas(buf, pagesize=A4)
    width, height = A4

    y = height - 30 * mm
    c.setFont("Helvetica-Bold", 16)
    c.drawString(25 * mm, y, "Salary Slip")
    y -= 15 * mm

    c.setFont("Helvetica", 12)
    lines = [
        f"Name: {full_name}",
        f"Employee ID (code): {employee_code}",
        f"CNP: {cnp}",
        f"Month: {month_label}",
        "",
        f"Base salary: {base_salary:.2f} RON",
        f"Working days: {working_days}",
        f"Vacation days: {vacation_days}",
        f"Bonuses: {bonus_total:.2f} RON",
        "",
        f"Total salary to be paid: {total_salary:.2f} RON",
    ]
    for line in lines:
        c.drawString(25 * mm, y, line)
        y -= 8 * mm

    c.setFont("Helvetica-Oblique", 9)
    c.drawString(25 * mm, 20 * mm, "This PDF is password-protected. Password = employee CNP.")
    c.showPage()
    c.save()

    raw_pdf = buf.getvalue()

    reader = PdfReader(io.BytesIO(raw_pdf))
    writer = PdfWriter()
    for page in reader.pages:
        writer.add_page(page)
    writer.encrypt(user_password=cnp, owner_password=cnp)

    out = io.BytesIO()
    writer.write(out)
    return out.getvalue()


# ---------- Endpoints ----------
@router.post("/createPdfForEmployees")
@with_idempotency("createPdfForEmployees")
def create_pdfs_for_employees(
    manager: User = Depends(require_manager),
    db: Session = Depends(get_db),
    request: Request = None,
):
    today = date.today()
    mstart, mend = month_bounds(today)
    month_label = today.strftime("%B %Y")
    out_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "storage", "pdf"))
    os.makedirs(out_dir, exist_ok=True)

    employees = db.scalars(
        select(User).where(User.role == ModelRole.employee, User.manager_id == manager.id)
        .order_by(User.last_name, User.first_name)
    ).all()
    if not employees:
        raise HTTPException(status_code=404, detail="No employees for this manager")

    files = []
    for emp in employees:
        data = calc_current_month_salary(db, emp.id, mstart, mend)
        full_name = f"{emp.first_name} {emp.last_name}"
        pdf_bytes = gen_pdf_bytes(
            full_name=full_name,
            employee_code=emp.employee_code,
            cnp=emp.cnp,
            month_label=month_label,
            base_salary=data["base_salary"],
            working_days=data["working_days"],
            vacation_days=data["vacation_days"],
            bonus_total=data["bonus_total"],
            total_salary=data["total_salary"],
        )
        fname = f"slip_{emp.id}_{today.strftime('%Y%m')}.pdf"
        fpath = os.path.join(out_dir, fname)
        with open(fpath, "wb") as f:
            f.write(pdf_bytes)
        files.append(fpath)

    return {"ok": True, "files": files, "count": len(files), "month": today.strftime("%Y-%m")}


@router.post("/sendPdfToEmployees")
@with_idempotency("sendPdfToEmployees")
def send_pdfs_to_employees(
    manager: User = Depends(require_manager),
    db: Session = Depends(get_db),
    request: Request = None,
):
    today = date.today()
    month_tag = today.strftime("%Y%m")
    month_label = today.strftime("%B %Y")
    pdf_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "storage", "pdf"))
    os.makedirs(pdf_dir, exist_ok=True)

    # Ensure PDFs exist (generate if missing)
    _ = create_pdfs_for_employees(manager=manager, db=db, request=request)

    sent = []
    employees = db.scalars(
        select(User).where(User.role == ModelRole.employee, User.manager_id == manager.id)
    ).all()

    for emp in employees:
        fname = f"slip_{emp.id}_{month_tag}.pdf"
        path = os.path.join(pdf_dir, fname)
        if not os.path.exists(path):
            continue

        with open(path, "rb") as f:
            pdf_bytes = f.read()

        subject = f"Your Salary Slip - {month_label}"
        body = (
            f"Hello {emp.first_name},\n\n"
            f"Attached is your salary slip for {month_label}.\n"
            f"The PDF is password-protected with your CNP.\n\n"
            f"Regards,\nSlip Salary App"
        )
        send_email(
            smtp_host=settings.smtp_host,
            smtp_port=settings.smtp_port,
            subject=subject,
            sender="noreply@slip-salary.local",
            recipients=[emp.email],
            body=body,
            attachments=[(fname, pdf_bytes, "application/pdf")],
        )
        sent.append({"employee": f"{emp.first_name} {emp.last_name}", "email": emp.email, "file": path})

    # Archive after sending
    archive_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "storage", "archive", "pdf"))
    os.makedirs(archive_dir, exist_ok=True)
    for item in sent:
        src = item["file"]
        base = os.path.basename(src)
        dst = os.path.join(archive_dir, f"{base.removesuffix('.pdf')}_{today.strftime('%Y%m%d')}.pdf")
        shutil.copy2(src, dst)
        item["archived_as"] = dst

    return {"ok": True, "sent": sent, "count": len(sent), "month": today.strftime("%Y-%m")}