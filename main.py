from pathlib import Path
from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

BASE_DIR = Path(__file__).resolve().parent
STATIC_DIR = BASE_DIR / "static"

app = FastAPI(title="RITA Instagram Guardian", version="0.1.0")
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")


@app.get("/")
def dashboard():
    return FileResponse(STATIC_DIR / "index.html")


@app.get("/api/health")
def health():
    return {
        "status": "ok",
        "project": "RITA Instagram Guardian",
        "instagram_connected": False,
        "notice": "Dashboard prototype only; no Instagram actions are connected.",
    }


@app.get("/api/capabilities")
def capabilities():
    return {
        "manual_violation_log": True,
        "local_rules": True,
        "instagram_group_read": False,
        "delete_other_users_messages": False,
        "remove_group_members": False,
        "note": "Only add integrations supported by official Meta APIs and approved permissions.",
    }
