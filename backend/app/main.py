from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import os, uuid
from loguru import logger

from app.config import settings
from app.routers_auth import router as auth_router, manager_router as manager_router
from app.routers_reports import router as reports_router
from app.routers_pdfs import router as pdfs_router
from app.routers_archives import router as archives_router

app = FastAPI(title="Slip Salary API", version="1.0.0")

# CORS for the React app
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # tighten later if you want
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Simple request logging + correlation id
@app.middleware("http")
async def log_requests(request: Request, call_next):
    correlation_id = request.headers.get("X-Request-ID") or str(uuid.uuid4())
    idempotency_key = request.headers.get("Idempotency-Key")
    who = "anon"
    if (auth := request.headers.get("Authorization", "")) and auth.lower().startswith("bearer "):
        who = "bearer"
    logger.info(f"[{correlation_id}] {request.method} {request.url.path} Idem={idempotency_key} User={who}")
    response: Response = await call_next(request)
    response.headers["X-Request-ID"] = correlation_id
    return response

# Routers
app.include_router(auth_router)
app.include_router(manager_router)   # /manager/ping
app.include_router(reports_router)   # CSV create/send
app.include_router(pdfs_router)      # PDF create/send
app.include_router(archives_router)  # list archives

# Serve generated files (CSV/PDF/archives)
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
STORAGE_DIR = os.path.join(BASE_DIR, "storage")
os.makedirs(STORAGE_DIR, exist_ok=True)
app.mount("/files", StaticFiles(directory=STORAGE_DIR), name="files")

@app.get("/health")
def health():
    return {
        "status": "ok",
        "env": getattr(settings, "app_env", "dev"),
        "smtp": f"{getattr(settings, 'smtp_host', 'localhost')}:{getattr(settings, 'smtp_port', 1025)}",
    }
