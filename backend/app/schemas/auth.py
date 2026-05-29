from pydantic import BaseModel


class LoginRequest(BaseModel):
    username: str


class LoginResponse(BaseModel):
    question: str


class VerifyRequest(BaseModel):
    answer: str
    phone: str


class VerifyResponse(BaseModel):
    session_id: str
    message: str = "Código enviado por Telegram"


class ConfirmRequest(BaseModel):
    session_id: str
    code: str


class ConfirmResponse(BaseModel):
    token: str
    user: str
