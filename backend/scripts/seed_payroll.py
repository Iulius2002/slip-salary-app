from datetime import date, timedelta
import calendar

from sqlalchemy.orm import Session
from sqlalchemy import select
from app.db import SessionLocal
from app.models import User, Vacation, Bonus, WorkLog

def first_last_day_of_month(d: date):
    first = d.replace(day=1)
    last = d.replace(day=calendar.monthrange(d.year, d.month)[1])
    return first, last

def weekdays_in_range(start: date, end: date):
    cur = start
    while cur <= end:
        if cur.weekday() < 5:  # 0=Mon..4=Fri
            yield cur
        cur += timedelta(days=1)

def get_user_by_email(db: Session, email: str) -> User | None:
    return db.scalar(select(User).where(User.email == email))

def ensure_vacation(db: Session, user_id: int, start: date, end: date):
    # compute days as inclusive difference on weekdays only
    days = sum(1 for d in weekdays_in_range(start, end))
    v = Vacation(user_id=user_id, start_date=start, end_date=end, days=days)
    db.add(v)

def ensure_bonus(db: Session, user_id: int, day: date, amount: float, reason: str):
    b = Bonus(user_id=user_id, bonus_date=day, amount=amount, reason=reason)
    db.add(b)

def ensure_worklogs(db: Session, user_id: int, start: date, end: date, skip_days:set[date]):
    for d in weekdays_in_range(start, end):
        if d in skip_days:
            continue
        # 8h default
        existing = db.scalar(select(WorkLog).where(WorkLog.user_id == user_id, WorkLog.work_date == d))
        if not existing:
            db.add(WorkLog(user_id=user_id, work_date=d, hours=8))

def main():
    today = date.today()
    first, last = first_last_day_of_month(today)

    db = SessionLocal()
    try:
        mgr = get_user_by_email(db, "manager@example.com")
        alice = get_user_by_email(db, "alice@example.com")
        bob = get_user_by_email(db, "bob@example.com")

        if not all([mgr, alice, bob]):
            print("Seed users first (scripts/seed_users.py).")
            return

        # Alice: vacation 2 days mid-month, bonus 500
        alice_vac_start = first + timedelta(days=7)   # roughly 8th
        alice_vac_end   = alice_vac_start + timedelta(days=1)  # 2 days (weekdays assumed)
        ensure_vacation(db, alice.id, alice_vac_start, alice_vac_end)
        ensure_bonus(db, alice.id, first, 500, "Project bonus")
        alice_skip = {alice_vac_start, alice_vac_end}

        # Bob: vacation 1 day later in month, no bonus
        bob_vac = first + timedelta(days=14)  # ~15th
        ensure_vacation(db, bob.id, bob_vac, bob_vac)
        bob_skip = {bob_vac}

        # Create work logs for first 15 weekdays of the month (or up to 'today')
        wl_end = min(first + timedelta(days=20), last)  # ~first 3 weeks
        ensure_worklogs(db, alice.id, first, wl_end, alice_skip)
        ensure_worklogs(db, bob.id, first, wl_end, bob_skip)

        db.commit()
        print("Seeded payroll data for current month.")
    finally:
        db.close()

if __name__ == "__main__":
    main()
