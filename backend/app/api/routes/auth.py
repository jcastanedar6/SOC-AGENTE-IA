from datetime import datetime, timedelta, timezone

import jwt
from fastapi import APIRouter, HTTPException

from app.config import settings
from app.schemas.auth import (
    LoginRequest, LoginResponse,
    VerifyRequest, VerifyResponse,
    ConfirmRequest, ConfirmResponse,
)
from app.auth.codes import create_session, verify_code
from app.auth.telegram import send_code

router = APIRouter()


def _phone_to_chat_id(phone: str) -> str | None:
    phones = settings.auth_allowed_phone_list
    chats = settings.telegram_chat_id_list
    for p, c in zip(phones, chats):
        if p == phone.strip():
            return c
    return None


def _build_jwt(phone: str) -> str:
    expire = datetime.now(timezone.utc) + timedelta(minutes=settings.auth_jwt_expire_minutes)
    return jwt.encode(
        {"sub": settings.auth_username, "phone": phone, "exp": expire},
        settings.auth_secret_key,
        algorithm="HS256",
    )


@router.post("/login", response_model=LoginResponse)
def login(payload: LoginRequest):
    if payload.username != settings.auth_username:
        raise HTTPException(status_code=401, detail="Usuario incorrecto")
    return LoginResponse(question=settings.auth_secret_question)


@router.post("/verify", response_model=VerifyResponse)
async def verify(payload: VerifyRequest):
    if payload.answer.strip().lower() != settings.auth_secret_answer.strip().lower():
        raise HTTPException(status_code=401, detail="Respuesta incorrecta")

    allowed = settings.auth_allowed_phone_list
    if allowed and payload.phone.strip() not in allowed:
        raise HTTPException(status_code=401, detail="Teléfono no autorizado")

    session_id, code = create_session(payload.phone.strip())

    chat_id = _phone_to_chat_id(payload.phone.strip())
    if chat_id:
        sent = await send_code(chat_id, code)
        if not sent:
            raise HTTPException(status_code=500, detail="Error al enviar código por Telegram")

    return VerifyResponse(session_id=session_id)


@router.post("/confirm", response_model=ConfirmResponse)
def confirm(payload: ConfirmRequest):
    phone = verify_code(payload.session_id, payload.code.strip())
    if not phone:
        raise HTTPException(status_code=401, detail="Código inválido o expirado")

    token = _build_jwt(phone)
    return ConfirmResponse(token=token, user=settings.auth_username)
