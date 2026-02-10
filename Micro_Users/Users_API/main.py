import os
from dotenv import load_dotenv
from pathlib import Path
from fastapi import FastAPI, HTTPException, Form, Request, Response
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
from Users_Aplication.Handlers.Queries.FindUserByIDHandler import FindUserByIdHandler
from Users_Aplication.DTOs.UpdateUserDTO import UpdateUserDTO
from Users_Aplication.DTOs.LoginDTO import LoginDTO
from Users_Aplication.DTOs.RefreshTokenDTO import RefreshTokenDTO
from Users_Aplication.DTOs.TokenDTO import TokenDTO
from Users_Aplication.Commands.CreateUserCommand import CreateUserCommand
from Users_Aplication.Commands.UpdateUserCommand import UpdateUserCommand
from Users_Aplication.Commands.LoginCommand import LoginCommand
from Users_Aplication.Commands.RefreshTokenCommand import RefreshTokenCommand
from Users_Aplication.Queries.FindUserByIDQuerie import FindUserByIdQuery
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

    if not all([url, realm, client_id]):
        raise RuntimeError(
            "Missing Keycloak configuration in environment. Set KEYCLOAK_URL, KEYCLOAK_REALM, KEYCLOAK_CLIENT_ID"
        )

    # Require client credentials for admin operations
    if not client_secret:
        raise RuntimeError(
            "Missing Keycloak client credentials. Set KEYCLOAK_CLIENT_SECRET"
        )

    return KeycloakAdapter(
        base_url=url,
        realm=realm,
        client_id=client_id,
        client_secret=client_secret,
    )


@asynccontextmanager
async def lifespan(app):
    global _adapter, create_handler, update_handler, find_handler, login_handler, refresh_handler
    _adapter = build_adapter_from_env()
    create_handler = CreateUserHandler(_adapter)
    update_handler = UpdateUserHandler(_adapter)
    find_handler = FindUserByIdHandler(_adapter)
    login_handler = LoginHandler(_adapter)
    refresh_handler = RefreshTokenHandler(_adapter)
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
    cedula: int = Form(...),
):
    # Build command from multipart/form-data fields
    cmd = CreateUserCommand(
        password=password, email=email, first_name=first_name, last_name=last_name, cedula=cedula
    )
    user_dto = Mediator.send(cmd)
    if not user_dto:
        raise HTTPException(status_code=500, detail="Failed to create user")
    return UserResponse(**user_dto.model_dump())


@Mediator.handler
def _update_handler_fn(request: UpdateUserCommand):
    return update_handler.handle(request)


@app.put("/users/{user_id}", response_model=UserResponse)
def update_user(user_id: str, payload: UpdateUserDTO):
    cmd = UpdateUserCommand(user_id=user_id, **payload.model_dump())
    user_dto = Mediator.send(cmd)
    if user_dto is None:
        raise HTTPException(status_code=404, detail="User not found or update failed")
    return UserResponse(**user_dto.model_dump())


@Mediator.handler
def _find_handler_fn(request: FindUserByIdQuery):
    return find_handler.handle(request)


@app.get("/users/{user_id}", response_model=UserResponse)
def find_user_by_id(user_id: str):
    query = FindUserByIdQuery(user_id=user_id)
    user_dto = Mediator.send(query)
    if not user_dto:
        raise HTTPException(status_code=404, detail="User not found")
    return UserResponse(**user_dto.model_dump())


@Mediator.handler
def _login_handler_fn(request: LoginCommand):
    return login_handler.handle(request)


@app.post("/auth/login", response_model=TokenDTO)
def login(payload: LoginDTO):
    cmd = LoginCommand(**payload.model_dump())
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


@app.get("/auth/validate")
def validate_token(request: Request):
    token = _extract_access_token(request)
    if not token:
        raise HTTPException(status_code=401, detail="Missing token")

    info = _adapter.validate_token(token)
    if not info:
        raise HTTPException(status_code=401, detail="Invalid token")

    return Response(status_code=204)





if __name__ == "__main__":
    import uvicorn
        #el reload colocalo en true cuando estes en desarrollo
    uvicorn.run("Micro_Users.Users_API.main:app", host="127.0.0.1", port=8001, reload=False)
