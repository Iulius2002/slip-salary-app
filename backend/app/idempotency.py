from fastapi import Request
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from sqlalchemy import select
from typing import Callable, Any
from functools import wraps
import inspect

from app.db import SessionLocal
from app.models import IdempotencyRecord

def with_idempotency(endpoint_name: str):
    """
    Decorate endpoints so the same Idempotency-Key returns the same stored response.
    Works with both sync and async route functions that return JSON-serializable dicts.
    """
    def decorator(func: Callable[..., Any]):
        is_async = inspect.iscoroutinefunction(func)

        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Try to grab Request (so we can read headers)
            request: Request | None = None
            for v in kwargs.values():
                if isinstance(v, Request):
                    request = v
                    break
            if request is None:
                for v in args:
                    if isinstance(v, Request):
                        request = v
                        break

            id_key = None
            if request:
                id_key = request.headers.get("Idempotency-Key")

            # If no key, just run the function normally
            if not id_key:
                if is_async:
                    return await func(*args, **kwargs)
                else:
                    return func(*args, **kwargs)

            db: Session = SessionLocal()
            try:
                # If we already have a record for this key, return it immediately
                existing = db.scalar(select(IdempotencyRecord).where(IdempotencyRecord.key == id_key))
                if existing:
                    return JSONResponse(existing.response_json, status_code=existing.status_code)

                # Run the endpoint (support sync/async)
                if is_async:
                    result = await func(*args, **kwargs)
                else:
                    result = func(*args, **kwargs)

                # Normalize the result for storage
                status_code = 200
                payload: Any = result
                # If it's a Starlette Response, don't try to store raw body; just return it.
                if hasattr(result, "status_code") and hasattr(result, "body"):
                    return result  # skip storing complex responses

                # Store the response JSON
                rec = IdempotencyRecord(
                    key=id_key,
                    endpoint=endpoint_name,
                    status_code=status_code,
                    response_json=payload if isinstance(payload, dict) else {"result": payload},
                )
                db.add(rec)
                db.commit()

                return result
            finally:
                db.close()

        return wrapper
    return decorator
