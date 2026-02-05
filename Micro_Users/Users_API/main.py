import os
from dotenv import load_dotenv
from pathlib import Path
from fastapi import FastAPI, HTTPException, Form, Body
from fastapi.responses import StreamingResponse, JSONResponse
from pydantic import BaseModel, EmailStr
from typing import Optional, Dict, Any

# Load environment variables from the repository .env file (Micro_Users/.env)
env_path = Path(__file__).resolve().parent.parent / ".env"
if env_path.exists():
    load_dotenv(env_path)

from Users_Infraestruture.keycloak_adapter import KeycloakAdapter
from Users_Aplication.Handlers.Commands.CreateUserHandler import CreateUserHandler
from Users_Aplication.Handlers.Commands.UpdateUserHandler import UpdateUserHandler
from Users_Aplication.Handlers.Commands.LoginHandler import LoginHandler
from Users_Aplication.Handlers.Commands.RefreshTokenHandler import RefreshTokenHandler
from Users_Aplication.Handlers.Commands.RegisterTotpDeviceHandler import RegisterTotpDeviceHandler
from Users_Aplication.Handlers.Commands.VerifyTotpHandler import VerifyTotpHandler
from Users_Aplication.Handlers.Queries.FindUserByIDHandler import FindUserByIdHandler
from Users_Aplication.DTOs.UserDTO import UserDTO
from Users_Aplication.DTOs.UpdateUserDTO import UpdateUserDTO
from Users_Aplication.DTOs.AuthDTO import LoginDTO, RefreshTokenDTO, TotpRegisterDTO, TotpRegisterResponseDTO
from Users_Aplication.DTOs.TokenDTO import TokenDTO
from Users_Aplication.Commands.CreateUserCommand import CreateUserCommand
from Users_Aplication.Commands.UpdateUserCommand import UpdateUserCommand
from Users_Aplication.Commands.LoginCommand import LoginCommand
from Users_Aplication.Commands.VerifyTotpCommand import VerifyTotpCommand
from Users_Aplication.Commands.RefreshTokenCommand import RefreshTokenCommand
from Users_Aplication.Commands.RegisterTotpDeviceCommand import RegisterTotpDeviceCommand
from Users_Aplication.Commands.VerifyTotpCommand import VerifyTotpCommand
from Users_Aplication.DTOs.AuthDTO import TotpVerifyDTO, TotpVerifyResponseDTO
from Users_Aplication.Queries.FindUserByIDQuerie import FindUserByIdQuery
from Users_Domain.Exceptions.exceptions import (
    UserNotFoundException
)
import io
import qrcode
from contextlib import asynccontextmanager

# use mediatr library
from mediatr import Mediator


# Requests removed: endpoints now accept Command/Query models directly via Mediator


class UserResponse(BaseModel):
    id: Optional[str]
    username: Optional[str]
    email: Optional[EmailStr] = None
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    attributes: Optional[Dict[str, Any]] = None


def build_adapter_from_env() -> KeycloakAdapter:
    url = os.environ.get("KEYCLOAK_URL")
    realm = os.environ.get("KEYCLOAK_REALM")
    client_id = os.environ.get("KEYCLOAK_CLIENT_ID")
    # Prefer client credentials (client secret). Admin username/password are optional.
    client_secret = os.environ.get("KEYCLOAK_CLIENT_SECRET")
    admin_user = os.environ.get("KEYCLOAK_ADMIN_USER")
    admin_pass = os.environ.get("KEYCLOAK_ADMIN_PASS")

    if not all([url, realm, client_id]):
        raise RuntimeError(
            "Missing Keycloak configuration in environment. Set KEYCLOAK_URL, KEYCLOAK_REALM, KEYCLOAK_CLIENT_ID"
        )

    # Require either a client secret (preferred) or admin credentials
    if not (client_secret or (admin_user and admin_pass)):
        raise RuntimeError(
            "Missing Keycloak admin credentials. Set either KEYCLOAK_CLIENT_SECRET or both KEYCLOAK_ADMIN_USER and KEYCLOAK_ADMIN_PASS"
        )

    return KeycloakAdapter(
        base_url=url,
        realm=realm,
        client_id=client_id,
        client_secret=client_secret,
        admin_user=admin_user,
        admin_password=admin_pass,
    )


@asynccontextmanager
async def lifespan(app):
    global _adapter, create_handler, update_handler, find_handler, login_handler, refresh_handler, totp_handler, verify_handler
    _adapter = build_adapter_from_env()
    create_handler = CreateUserHandler(_adapter)
    update_handler = UpdateUserHandler(_adapter)
    find_handler = FindUserByIdHandler(_adapter)
    login_handler = LoginHandler(_adapter)
    refresh_handler = RefreshTokenHandler(_adapter)
    totp_handler = RegisterTotpDeviceHandler(_adapter)
    verify_handler = VerifyTotpHandler(_adapter)
    # no manual registration needed when using Mediator.handler decorators
    yield


from Users_API.middleware import DomainExceptionMiddleware


app = FastAPI(title="Users - Keycloak Adapter API", lifespan=lifespan)
app.add_middleware(DomainExceptionMiddleware)



@Mediator.handler
def _create_handler_fn(request: CreateUserCommand):
    return create_handler.handle(request)


@app.post("/users", response_model=UserResponse)
def create_user(
    password: str = Form(...),
    email: EmailStr = Form(...),
    first_name: str = Form(...),
    last_name: str = Form(...),
    cedula: float = Form(...),
):
    # Build command from multipart/form-data fields
    cmd = CreateUserCommand(
        password=password, email=email, first_name=first_name, last_name=last_name, cedula=cedula
    )
    user_dto = Mediator.send(cmd)
    if not user_dto:
        raise HTTPException(status_code=500, detail="Failed to create user")
    return UserResponse(**user_dto.dict())


@Mediator.handler
def _update_handler_fn(request: UpdateUserCommand):
    return update_handler.handle(request)


@app.put("/users/{user_id}", response_model=UserResponse)
def update_user(user_id: str, payload: UpdateUserDTO):
    cmd = UpdateUserCommand(user_id=user_id, **payload.dict())
    user_dto = Mediator.send(cmd)
    if user_dto is None:
        raise HTTPException(status_code=404, detail="User not found or update failed")
    return UserResponse(**user_dto.dict())


@Mediator.handler
def _find_handler_fn(request: FindUserByIdQuery):
    return find_handler.handle(request)


@app.get("/users/{user_id}", response_model=UserResponse)
def find_user_by_id(user_id: str):
    query = FindUserByIdQuery(user_id=user_id)
    user_dto = Mediator.send(query)
    if not user_dto:
        raise HTTPException(status_code=404, detail="User not found")
    return UserResponse(**user_dto.dict())


@Mediator.handler
def _login_handler_fn(request: LoginCommand):
    return login_handler.handle(request)


@app.post("/auth/login", response_model=TokenDTO)
def login(payload: LoginDTO):
    cmd = LoginCommand(**payload.dict())
    try:
        token = Mediator.send(cmd)
    except Exception:
        raise HTTPException(status_code=401, detail="Invalid credentials")
    return token


@Mediator.handler
def _refresh_handler_fn(request: RefreshTokenCommand):
    return refresh_handler.handle(request)


@app.post("/auth/refresh", response_model=TokenDTO)
def refresh_token(payload: RefreshTokenDTO):
    cmd = RefreshTokenCommand(**payload.dict())
    try:
        token = Mediator.send(cmd)
    except Exception:
        raise HTTPException(status_code=401, detail="Invalid refresh token")
    return token


@Mediator.handler
def _register_totp_handler_fn(request: RegisterTotpDeviceCommand):
    return totp_handler.handle(request)


@Mediator.handler
def _verify_totp_handler_fn(request: VerifyTotpCommand):
    return verify_handler.handle(request)


@app.post("/users/{user_id}/totp/register", response_model=TotpRegisterResponseDTO)
def register_totp_device(user_id: str, payload: TotpRegisterDTO = Body(default=TotpRegisterDTO())):
    cmd = RegisterTotpDeviceCommand(user_id=user_id, device_name=payload.device_name)
    try:
        result = Mediator.send(cmd)
    except UserNotFoundException:
        raise HTTPException(status_code=404, detail="User not found")
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to register TOTP device: {e}")
    result.qr_code_url = f"/users/{user_id}/totp/qr"
    return result


@app.post("/users/{user_id}/totp/verify", response_model=TotpVerifyResponseDTO)
def verify_totp(user_id: str, payload: TotpVerifyDTO = Body(...)):
    cmd = VerifyTotpCommand(user_id=user_id, code=payload.code, secret=payload.secret)
    try:
        result = Mediator.send(cmd)
    except UserNotFoundException:
        raise HTTPException(status_code=404, detail="User not found")
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"TOTP verification failed: {e}")
    return result


@app.get("/users/{user_id}/totp/qr")
def totp_qr(user_id: str):
    try:
        user_info = _adapter.find_user_by_id(user_id)
    except UserNotFoundException:
        raise HTTPException(status_code=404, detail="User not found")
    # Robustly extract the secret from attributes (Keycloak may store as list or string)
    attrs = user_info.get("attributes") or {}
    secret = None
    for key in ("otpSecret", "otpsecret", "otp_secret", "otp"):
        if key in attrs:
            val = attrs.get(key)
            if isinstance(val, list) and len(val) > 0:
                secret = val[0]
            elif isinstance(val, str):
                secret = val
            break

    if not secret:
        secret = _adapter.get_cached_totp_secret(user_id)

    # If still not found, try some common fallbacks (some setups store in 'otp' credentials)
    if not secret:
        # Return helpful debug output instead of opaque 404
        return JSONResponse(
            status_code=404,
            content={
                "detail": "TOTP secret not found",
                "attributes": attrs,
                "user_info_sample": {
                    "id": user_info.get("id"),
                    "username": user_info.get("username"),
                    "email": user_info.get("email"),
                },
            },
        )

    issuer = _adapter.realm
    account = user_info.get("email") or user_info.get("username") or user_id
    otpauth_url = "otpauth://totp/{issuer}:{account}?secret={secret}&issuer={issuer}".format(
        issuer=issuer, account=account, secret=secret
    )

    qr = qrcode.QRCode(box_size=6, border=2)
    qr.add_data(otpauth_url)
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white")
    buffer = io.BytesIO()
    img.save(buffer, format="PNG")
    buffer.seek(0)
    return StreamingResponse(buffer, media_type="image/png")


@app.get("/users/{user_id}/totp/debug")
def totp_debug(user_id: str):
    """Return user attributes to help debug TOTP registration issues (dev endpoint)."""
    try:
        user_info = _adapter.find_user_by_id(user_id)
    except UserNotFoundException:
        raise HTTPException(status_code=404, detail="User not found")
    attrs = user_info.get("attributes") or {}
    return JSONResponse(status_code=200, content={"attributes": attrs, "user_info": {"id": user_info.get("id"), "username": user_info.get("username"), "email": user_info.get("email")}})



if __name__ == "__main__":
    import uvicorn
        #el reload colocalo en true cuando estes en desarrollo
    uvicorn.run("Micro_Users.Users_API.main:app", host="0.0.0.0", port=8500, reload=False)
