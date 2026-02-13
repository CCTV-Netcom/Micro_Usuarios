from fastapi import APIRouter, HTTPException, Form, Request, Response
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
def update_user(user_id: str, payload: UpdateUserDTO):
    cmd = UpdateUserCommand(user_id=user_id, **payload.model_dump())
    user_dto = Mediator.send(cmd)
    if user_dto is None:
        raise HTTPException(status_code=404, detail="User not found or update failed")
    return UserResponse(**user_dto.model_dump())


@router.get("/users/{user_id}", response_model=UserResponse, summary="Obtener usuario", description="Devuelve la información del usuario por su ID.", tags=["Usuarios"])
def find_user_by_id(user_id: str):
    query = FindUserByIdQuery(user_id=user_id)
    user_dto = Mediator.send(query)
    if not user_dto:
        raise HTTPException(status_code=404, detail="User not found")
    return UserResponse(**user_dto.model_dump())


@router.post("/auth/login", response_model=TokenDTO, summary="Login", description="Inicia sesión y devuelve un token de acceso.", tags=["Auth"])
def login(payload: LoginDTO):
    cmd = LoginCommand(**payload.model_dump())
    try:
        token = Mediator.send(cmd)
    except Exception:
        raise HTTPException(status_code=401, detail="Invalid credentials")
    return token


@router.post("/auth/refresh", response_model=TokenDTO, summary="Refresh token", description="Renueva el token de acceso usando el refresh token.", tags=["Auth"])
def refresh_token(payload: RefreshTokenDTO):
    cmd = RefreshTokenCommand(**payload.model_dump())
    try:
        token = Mediator.send(cmd)
    except Exception:
        raise HTTPException(status_code=401, detail="Invalid refresh token")
    return token


def _extract_access_token(request: Request) -> str:
    auth_header = request.headers.get("Authorization")
    if auth_header and auth_header.lower().startswith("bearer "):
        return auth_header.split(" ", 1)[1].strip()
    return request.cookies.get("access_token") or request.cookies.get("authToken") or ""


@router.get("/auth/validate", summary="Validar token", description="Valida el token de acceso enviado en header o cookie.", tags=["Auth"])
def validate_token(request: Request):
    token = _extract_access_token(request)
    if not token:
        raise HTTPException(status_code=401, detail="Missing token")

    adapter = request.app.state.adapter
    info = adapter.validate_token(token)
    if not info:
        raise HTTPException(status_code=401, detail="Invalid token")

    return Response(status_code=204)
