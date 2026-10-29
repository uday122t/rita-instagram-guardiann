import os
import sqlite3
from pathlib import Path
from urllib.parse import urlencode

import httpx
from cryptography.fernet import Fernet
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import FileResponse, RedirectResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from itsdangerous import URLSafeTimedSerializer, BadSignature, SignatureExpired

load_dotenv()
BASE_DIR = Path(__file__).resolve().parent
STATIC_DIR = BASE_DIR / "static"
DB_PATH = BASE_DIR / "rita.sqlite3"

app = FastAPI(title="RITA Instagram Guardian", version="0.2.0")
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")

APP_ID = os.getenv("META_APP_ID", "").strip()
APP_SECRET = os.getenv("META_APP_SECRET", "").strip()
REDIRECT_URI = os.getenv("META_REDIRECT_URI", "").strip()
APP_SIGNING_SECRET = os.getenv("APP_SIGNING_SECRET", "").strip()
TOKEN_ENCRYPTION_KEY = os.getenv("TOKEN_ENCRYPTION_KEY", "").strip()
SCOPES = "instagram_business_basic,instagram_business_manage_messages"


def db():
    conn = sqlite3.connect(DB_PATH)
    conn.execute("CREATE TABLE IF NOT EXISTS settings (key TEXT PRIMARY KEY, value TEXT NOT NULL)")
    conn.commit()
    return conn


def save_encrypted_token(token: str):
    if not TOKEN_ENCRYPTION_KEY:
        raise RuntimeError("TOKEN_ENCRYPTION_KEY is not configured")
    encrypted = Fernet(TOKEN_ENCRYPTION_KEY.encode()).encrypt(token.encode()).decode()
    with db() as conn:
        conn.execute(
            "INSERT INTO settings(key,value) VALUES('instagram_token',?) "
            "ON CONFLICT(key) DO UPDATE SET value=excluded.value",
            (encrypted,),
        )


def is_connected():
    with db() as conn:
        row = conn.execute("SELECT value FROM settings WHERE key='instagram_token'").fetchone()
    return bool(row)


def oauth_ready():
    return all([APP_ID, APP_SECRET, REDIRECT_URI, APP_SIGNING_SECRET, TOKEN_ENCRYPTION_KEY])


@app.get("/")
def dashboard():
    return FileResponse(STATIC_DIR / "index.html")


@app.get("/api/health")
def health():
    return {
        "status": "ok",
        "project": "RITA Instagram Guardian",
        "instagram_connected": is_connected(),
        "instagram_username": "rita_.core",
        "notice": "Official Instagram OAuth connection; group moderation is not supported by the official API.",
    }


@app.get("/api/capabilities")
def capabilities():
    return {
        "official_instagram_login": True,
        "manual_violation_log": True,
        "local_rules": True,
        "instagram_group_read": False,
        "delete_other_users_messages": False,
        "remove_group_members": False,
        "note": "Instagram messaging API does not provide group chat moderation.",
    }


@app.get("/auth/instagram")
def instagram_login():
    if not oauth_ready():
        return JSONResponse(
            status_code=503,
            content={"error": "يجب إعداد بيانات تطبيق Meta ومفاتيح الحماية في متغيرات البيئة أولاً."},
        )
    state = URLSafeTimedSerializer(APP_SIGNING_SECRET, salt="rita-instagram-oauth").dumps(os.urandom(24).hex())
    url = "https://www.instagram.com/oauth/authorize?" + urlencode({
        "client_id": APP_ID,
        "redirect_uri": REDIRECT_URI,
        "response_type": "code",
        "scope": SCOPES,
        "state": state,
        "enable_fb_login": "0",
        "force_authentication": "1",
    })
    response = RedirectResponse(url, status_code=302)
    response.set_cookie("rita_oauth_state", state, httponly=True, secure=REDIRECT_URI.startswith("https://"), samesite="lax", max_age=600)
    return response


@app.get("/auth/callback")
async def instagram_callback(request: Request, code: str = "", state: str = "", error: str = ""):
    if error:
        return RedirectResponse("/?instagram=cancelled", status_code=303)
    cookie_state = request.cookies.get("rita_oauth_state")
    if not code or not state or not cookie_state or state != cookie_state:
        raise HTTPException(status_code=400, detail="تعذر التحقق من جلسة تسجيل الدخول. حاول مرة أخرى.")
    try:
        URLSafeTimedSerializer(APP_SIGNING_SECRET, salt="rita-instagram-oauth").loads(state, max_age=600)
    except (BadSignature, SignatureExpired):
        raise HTTPException(status_code=400, detail="انتهت صلاحية محاولة تسجيل الدخول. حاول مرة أخرى.")

    async with httpx.AsyncClient(timeout=20) as client:
        token_response = await client.post(
            "https://api.instagram.com/oauth/access_token",
            data={
                "client_id": APP_ID,
                "client_secret": APP_SECRET,
                "grant_type": "authorization_code",
                "redirect_uri": REDIRECT_URI,
                "code": code,
            },
        )
        if token_response.is_error:
            raise HTTPException(status_code=502, detail="إنستغرام لم يقبل طلب الربط. راجع إعدادات تطبيق Meta.")
        token_data = token_response.json()
        access_token = token_data.get("access_token")
        if not access_token:
            raise HTTPException(status_code=502, detail="لم يرجع إنستغرام رمز وصول صالحاً.")

        long_response = await client.get(
            "https://graph.instagram.com/access_token",
            params={
                "grant_type": "ig_exchange_token",
                "client_secret": APP_SECRET,
                "access_token": access_token,
            },
        )
        if long_response.is_success and long_response.json().get("access_token"):
            access_token = long_response.json()["access_token"]

    try:
        save_encrypted_token(access_token)
    except Exception:
        raise HTTPException(status_code=500, detail="تم تسجيل الدخول لكن تعذر حفظ الاتصال الآمن. راجع إعدادات التشفير.")

    response = RedirectResponse("/?instagram=connected", status_code=303)
    response.delete_cookie("rita_oauth_state")
    return response
