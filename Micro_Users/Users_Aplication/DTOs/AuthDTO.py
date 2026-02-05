from pydantic import BaseModel
from typing import Optional


class LoginDTO(BaseModel):
    username: str
    password: str
    totp: Optional[str] = None


class RefreshTokenDTO(BaseModel):
    refresh_token: str


class TotpRegisterDTO(BaseModel):
    device_name: Optional[str] = None


class TotpRegisterResponseDTO(BaseModel):
    user_id: str
    required_action: str
    device_name: Optional[str] = None
    secret: str
    otpauth_url: str
    qr_code_url: Optional[str] = None
    qr_code_base64: Optional[str] = None
    configured: bool


class TotpVerifyDTO(BaseModel):
    code: str
    secret: Optional[str] = None


class TotpVerifyResponseDTO(BaseModel):
    success: bool
    message: Optional[str] = None
