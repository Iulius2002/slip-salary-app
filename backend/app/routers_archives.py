from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
import os, time

from app.db import SessionLocal
from app.routers_auth import require_manager

router = APIRouter(tags=["archives"])

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

BASE = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
ARCHIVE_CSV = os.path.join(BASE, "storage", "archive", "csv")
ARCHIVE_PDF = os.path.join(BASE, "storage", "archive", "pdf")

def list_dir(dirpath: str, base_url: str):
    os.makedirs(dirpath, exist_ok=True)
    items = []
    for name in sorted(os.listdir(dirpath), reverse=True):
        path = os.path.join(dirpath, name)
        if not os.path.isfile(path):
            continue
        st = os.stat(path)
        items.append({
            "name": name,
            "size_bytes": st.st_size,
            "modified": time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(st.st_mtime)),
            "url": f"{base_url}/{name}",
        })
    return items

@router.get("/archives")
def list_archives(_: str = Depends(require_manager), db: Session = Depends(get_db)):
    return {
        "csv": list_dir(ARCHIVE_CSV, "/files/archive/csv"),
        "pdf": list_dir(ARCHIVE_PDF, "/files/archive/pdf"),
    }

from fastapi.responses import HTMLResponse

@router.get("/archives/browse", response_class=HTMLResponse)
def browse_archives(_: str = Depends(require_manager)):
    # Very simple HTML list using the same listing helpers
    data = {
        "csv": list_dir(ARCHIVE_CSV, "/files/archive/csv"),
        "pdf": list_dir(ARCHIVE_PDF, "/files/archive/pdf"),
    }
    def li(items):
        return "\n".join(
            f'<li><a href="{f["url"]}" target="_blank">{f["name"]}</a> '
            f' <small>({f["modified"]}, {f["size_bytes"]} B)</small></li>'
            for f in items
        )
    html = f"""
    <html><body>
      <h1>Archives</h1>
      <h2>CSV</h2>
      <ul>{li(data["csv"]) or "<li>No archived CSV yet.</li>"}</ul>
      <h2>PDF</h2>
      <ul>{li(data["pdf"]) or "<li>No archived PDF yet.</li>"}</ul>
    </body></html>
    """
    return HTMLResponse(content=html, status_code=200)