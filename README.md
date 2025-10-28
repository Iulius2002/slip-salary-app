#  Slip Salary App

A full-stack payroll management system built with **FastAPI**, **PostgreSQL**, and **React (Vite + TypeScript)**.  
The app allows managers to generate and send salary slips (in CSV and PDF format) to employees, with built-in **authorization**, **idempotency**, **logging**, and **archiving**.

---

##  Tech Stack

### Backend
- **FastAPI** (Python)
- **SQLAlchemy + Alembic** (ORM + migrations)
- **PostgreSQL** (database)
- **MailHog** (test SMTP server)
- **Loguru** (structured logging)
- **Idempotency & role-based auth**
- **PDF and CSV generation**
- **Static serving for archives**

### Frontend
- **React (Vite + TypeScript)**
- **Axios** for API calls with `Bearer` + `Idempotency-Key`
- **Tailwind CSS**
- **Router-based navigation** (Login → Dashboard → Manager)

---

##  Features

✅ Employee and Manager roles  
✅ Manager-only actions (create/send reports)  
✅ Generate CSV summary of salaries  
✅ Send CSV to manager email  
✅ Generate password-protected PDFs per employee  
✅ Send PDFs to employees via MailHog  
✅ All files archived automatically under `/files/archive`  
✅ Safe retry with `Idempotency-Key`  
✅ Structured logging with correlation IDs  
✅ Simple Manager UI dashboard to trigger all actions  

---

## 🚀 Quick Start (Mac / Unix)

### 1️⃣ Clone the repo

```bash
git clone https://github.com/Iulius2002/slip-salary-app.git
cd slip-salary-app
```

### 2️⃣ Start Docker services (PostgreSQL + MailHog)

```bash
docker compose up -d
```
PostgreSQL → localhost:5432

MailHog → http://localhost:8025

### 3️⃣ Backend setup

````bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
alembic upgrade head

# Seed database with manager + employees
python -m scripts.seed_users

# Run backend
uvicorn app.main:app --reload
````
Backend now runs at → http://127.0.0.1:8000

### 4️⃣ Frontend setup

````bash
cd ../frontend
npm install
npm run dev
````
Frontend runs at → http://localhost:5173

##  Default Users


| Role       | Email               | Password  |
|-------------|---------------------|------------|
| Manager     | manager@example.com | Passw0rd!  |
| Employee 1  | alice@example.com   | Passw0rd!  |
| Employee 2  | bob@example.com     | Passw0rd!  |

##  Demo Flow

### 1️⃣ Log in at http://localhost:5173 as:
````bash
manager@example.com / Passw0rd!
````

### 2️⃣ You’ll be redirected to the Dashboard → click Go to Manager Dashboard.

### 3️⃣ Inside the Manager UI:
	•	Create CSV → generates a summary file for all employees under your management
	•	Send CSV (MailHog) → emails the CSV to your manager inbox (MailHog)
	•	Create PDFs → generates individual, password-protected salary slips (CNP = password)
	•	Send PDFs (MailHog) → emails the PDFs to each employee

### 4️⃣ Check MailHog:
👉 http://localhost:8025

### 5️⃣ Files are stored under:
``
backend/storage/archive/csv/
 backend/storage/archive/pdf/
``

You can also browse them:
👉 http://127.0.0.1:8000/archives/browse_public

##  REST API Overview

| Endpoint | Method | Role | Description |
|-----------|---------|------|-------------|
| `/auth/login` | POST | All | Authenticate user, returns JWT |
| `/auth/me` | GET | All | Get current user info |
| `/manager/ping` | GET | Manager | Test protected route |
| `/createAggregatedEmployeeData` | POST | Manager | Generate CSV summary |
| `/sendAggregatedEmployeeData` | POST | Manager | Send CSV via email |
| `/createPdfForEmployees` | POST | Manager | Generate PDFs for employees |
| `/sendPdfToEmployees` | POST | Manager | Send PDFs via email |
| `/archives` | GET | Manager | List archived CSV/PDF |
| `/archives/browse_public` | GET | Public | Simple HTML archive browser |

##  Architecture Notes

- Each heavy endpoint supports idempotency:
Add header Idempotency-Key: <uuid> to make retries safe.
- Each request is logged in backend/logs/app.log with:

````bash
[RequestID] METHOD PATH Idem=KEY User=bearer

````

- PDF files are password-protected using the employee’s CNP (personal ID).
- After sending, all generated files are archived automatically for audit.

##  Development Helpers

| Command | Description |
|----------|-------------|
| `docker compose logs -f` | Watch database & mail logs |
| `alembic revision --autogenerate -m "message"` | Create DB migration |
| `alembic upgrade head` | Apply migrations |
| `tail -f backend/logs/app.log` | Watch backend logs |
| `uvicorn app.main:app --reload` | Run backend dev server |
| `npm run dev` | Run frontend dev server |


##  Demo Checklist

✅ Manager login works

✅ Health check returns OK

✅ CSV created & visible in Archives

✅ CSV sent via MailHog

✅ PDFs created & archived

✅ PDFs sent (encrypted attachments)

✅ Archives section lists all files

✅ Logs contain correlation IDs

✅ No duplicate runs (Idempotency works)
