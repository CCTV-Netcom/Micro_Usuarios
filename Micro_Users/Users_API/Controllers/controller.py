import os

from fastapi import APIRouter, HTTPException, Form, Request, Response, Body, Depends
from fastapi.encoders import jsonable_encoder
from pydantic import BaseModel, EmailStr, Field, ValidationError
from typing import Optional, Dict, Any
from mediatr import Mediator

from Users_Application.DTOs.UpdateUserDTO import UpdateUserDTO
from Users_Application.DTOs.LoginDTO import LoginDTO
from Users_Application.DTOs.RefreshTokenDTO import RefreshTokenDTO
from Users_Application.DTOs.TokenDTO import TokenDTO
from Users_Application.Commands.CreateUserCommand import CreateUserCommand
from Users_Application.Commands.UpdateUserCommand import UpdateUserCommand
from Users_Application.Commands.LoginCommand import LoginCommand
from Users_Application.Commands.RefreshTokenCommand import RefreshTokenCommand
from Users_Application.Queries.FindUserByIDQuerie import FindUserByIdQuery
from Users_Domain.Enums.role import RoleEnum


class UserResponse(BaseModel):
    id: Optional[str] = Field(None, description="Identificador único del usuario")
    username: Optional[str] = Field(None, description="Nombre de usuario (login)")
    email: Optional[EmailStr] = Field(None, description="Correo electrónico del usuario")
    first_name: Optional[str] = Field(None, description="Nombre")
    last_name: Optional[str] = Field(None, description="Apellido")
    rol: Optional[str] = Field(None, description="Rol del usuario")
    attributes: Optional[Dict[str, Any]] = Field(None, description="Atributos adicionales del usuario")


router = APIRouter()

ACCESS_TOKEN_MAX_AGE = 60 * 60
REFRESH_TOKEN_MAX_AGE = 60 * 60 * 24 * 7
AUTH_COOKIE_SAMESITE = os.getenv("AUTH_COOKIE_SAMESITE", "none").lower()

if AUTH_COOKIE_SAMESITE not in {"lax", "strict", "none"}:
    AUTH_COOKIE_SAMESITE = "none"


class AuthSessionResponse(BaseModel):
    detail: str
    access_token: Optional[str] = None


def _set_auth_cookies(response: Response, token: TokenDTO) -> None:
    response.set_cookie(
        key="access_token",
        value=token.access_token,
        httponly=True,
        secure=True,
        samesite=AUTH_COOKIE_SAMESITE,
        max_age=ACCESS_TOKEN_MAX_AGE,
        path="/",
    )

    if token.refresh_token:
        response.set_cookie(
            key="refresh_token",
            value=token.refresh_token,
            httponly=True,
            secure=True,
            samesite=AUTH_COOKIE_SAMESITE,
            max_age=REFRESH_TOKEN_MAX_AGE,
            path="/",
        )


def _clear_auth_cookies(response: Response) -> None:
    response.delete_cookie(key="access_token", path="/")
    response.delete_cookie(key="refresh_token", path="/")
    response.delete_cookie(key="authToken", path="/")


def _extract_access_token(request: Request) -> str:
    """Obtiene bearer token desde header Authorization o cookies compatibles."""
    auth_header = request.headers.get("Authorization")
    if auth_header and auth_header.lower().startswith("bearer "):
        return auth_header.split(" ", 1)[1].strip()
    return request.cookies.get("access_token") or request.cookies.get("authToken") or ""


def require_auth(request: Request):
    """Dependency that validates access token using the app adapter.

    Raises HTTPException(401) when token missing or invalid.
    Returns adapter validation info on success.
    """
    token = _extract_access_token(request)
    if not token:
        raise HTTPException(status_code=401, detail="Missing token")

    adapter = request.app.state.adapter
    info = adapter.validate_token(token)
    if not info:
        raise HTTPException(status_code=401, detail="Invalid token")
    return info


@router.post(
    "/users",
    response_model=UserResponse,
    summary="Crear usuario",
    description="Crea un nuevo usuario con los campos especificados.",
    tags=["Usuarios"],
    responses={422: {"description": "Error de validación en los datos enviados"}},
)
def create_user(
    password: str = Form(...),
    email: EmailStr = Form(...),
    first_name: str = Form(...),
    last_name: str = Form(...),
    cedula: int = Form(...),
    rol: RoleEnum = Form(...),
):
    """Crea un usuario y retorna su representación pública."""
    cmd = CreateUserCommand(
        password=password,
        email=email,
        first_name=first_name,
        last_name=last_name,
        cedula=cedula,
        rol=rol,
    )
    try:
        user_dto = Mediator.send(cmd)
    except ValidationError as e:
        safe_errors = jsonable_encoder(
            e.errors(),
            custom_encoder={Exception: lambda exc: str(exc)},
        )
        raise HTTPException(status_code=422, detail=safe_errors)
    if not user_dto:
        raise HTTPException(status_code=500, detail="Failed to create user")
    return UserResponse(**user_dto.model_dump())


@router.put("/users/{user_id}", response_model=UserResponse, summary="Actualizar usuario", description="Actualiza campos del usuario especificado.", tags=["Usuarios"]) 
def update_user(user_id: str, payload: UpdateUserDTO, _auth: Any = Depends(require_auth)):
    """Actualiza un usuario por su identificador."""
    cmd = UpdateUserCommand(user_id=user_id, **payload.model_dump())
    user_dto = Mediator.send(cmd)
    if user_dto is None:
        raise HTTPException(status_code=404, detail="User not found or update failed")
    return UserResponse(**user_dto.model_dump())


@router.get("/users/{user_id}", response_model=UserResponse, summary="Obtener usuario", description="Devuelve la información del usuario por su ID.", tags=["Usuarios"])
def find_user_by_id(user_id: str, _auth: Any = Depends(require_auth)):
    """Busca un usuario por ID."""
    query = FindUserByIdQuery(user_id=user_id)
    user_dto = Mediator.send(query)
    if not user_dto:
        raise HTTPException(status_code=404, detail="User not found")
    return UserResponse(**user_dto.model_dump())


@router.post(
    "/auth/login",
    response_model=AuthSessionResponse,
    summary="Login",
    description="Inicia sesión y establece cookies seguras de autenticación.",
    tags=["Auth"],
)
def login(payload: LoginDTO, response: Response):
    """Autentica al usuario y establece cookies de sesión seguras."""
    cmd = LoginCommand(**payload.model_dump())
    try:
        token = Mediator.send(cmd)
    except Exception:
        raise HTTPException(status_code=401, detail="Invalid credentials")
    _set_auth_cookies(response, token)
    return AuthSessionResponse(detail="Login successful", access_token=token.access_token)


@router.post(
    "/auth/refresh",
    response_model=AuthSessionResponse,
    summary="Refresh token",
    description="Renueva la sesión usando refresh token desde body o cookie segura.",
    tags=["Auth"],
)
def refresh_token(
    request: Request,
    response: Response,
    payload: dict | None = Body(default=None),
):
    """Renueva cookies de sesión usando refresh token."""
    refresh_token_value = (payload or {}).get("refresh_token") or request.cookies.get("refresh_token", "")
    if not refresh_token_value:
        raise HTTPException(status_code=401, detail="Missing refresh token")

    cmd = RefreshTokenCommand(refresh_token=refresh_token_value)
    try:
        token = Mediator.send(cmd)
    except Exception:
        raise HTTPException(status_code=401, detail="Invalid refresh token")
    _set_auth_cookies(response, token)
    return AuthSessionResponse(detail="Session refreshed", access_token=token.access_token)


@router.post(
    "/auth/logout",
    response_model=AuthSessionResponse,
    summary="Logout",
    description="Cierra sesión y limpia cookies de autenticación.",
    tags=["Auth"],
)
def logout(response: Response):
    """Cierra la sesión actual borrando cookies de autenticación."""
    _clear_auth_cookies(response)
    return AuthSessionResponse(detail="Logout successful")



@router.get("/auth/validate", summary="Validar token", description="Valida el token de acceso enviado en header o cookie.", tags=["Auth"])
def validate_token(request: Request):
    """Valida token de acceso y responde 204 si es válido."""
    token = _extract_access_token(request)
    if not token:
        raise HTTPException(status_code=401, detail="Missing token")

    adapter = request.app.state.adapter
    info = adapter.validate_token(token)
    if not info:
        raise HTTPException(status_code=401, detail="Invalid token")

    return Response(status_code=204)
