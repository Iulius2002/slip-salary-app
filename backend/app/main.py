from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from loguru import logger
import uuid
from app.config import settings

app = FastAPI(title="Slip Salary API", version="0.1.0")

# CORS: allow the local React dev server
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://127.0.0.1:5173", "http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Logging + correlation ID + read Idempotency-Key
@app.middleware("http")
async def log_requests(request: Request, call_next):
    correlation_id = request.headers.get("X-Request-ID") or str(uuid.uuid4())
    idempotency_key = request.headers.get("Idempotency-Key")
    logger.info(f"[{correlation_id}] {request.method} {request.url} Idempotency-Key={idempotency_key}")
    response: Response = await call_next(request)
    response.headers["X-Request-ID"] = correlation_id
    return response

@app.get("/health")
def health():
    return {
        "status": "ok",
        "env": settings.app_env,
        "smtp": f"{settings.smtp_host}:{settings.smtp_port}"
    }