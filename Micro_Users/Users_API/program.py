import os
from dotenv import load_dotenv
from pathlib import Path
from contextlib import asynccontextmanager

from fastapi import FastAPI
from mediatr import Mediator

from Users_Infrastruture.keycloak_adapter import KeycloakAdapter
from Users_Application.Handlers.Commands.CreateUserHandler import CreateUserHandler
from Users_Application.Handlers.Commands.UpdateUserHandler import UpdateUserHandler
from Users_Application.Handlers.Commands.LoginHandler import LoginHandler
from Users_Application.Handlers.Commands.RefreshTokenHandler import RefreshTokenHandler
from Users_Application.Handlers.Queries.FindUserByIDHandler import FindUserByIdHandler
from Users_Application.Commands.CreateUserCommand import CreateUserCommand
from Users_Application.Commands.UpdateUserCommand import UpdateUserCommand
from Users_Application.Commands.LoginCommand import LoginCommand
from Users_Application.Commands.RefreshTokenCommand import RefreshTokenCommand
from Users_Application.Queries.FindUserByIDQuerie import FindUserByIdQuery

from .middleware import DomainExceptionMiddleware
from .Controllers.controller import router as users_router


# Carga variables de entorno desde Micro_Users/.env.
env_path = Path(__file__).resolve().parent.parent / ".env"
if env_path.exists():
    load_dotenv(env_path)
#este archivo se encarga de configurar la app, usa el patron singlenton para crear una instancia de Keycloak y los handlers
# y los registra en el Mediator para que puedan ser usados en los controladores (routers)

def build_adapter_from_env() -> KeycloakAdapter:
    """Construye el adaptador de Keycloak a partir de variables de entorno requeridas."""
    url = os.environ.get("KEYCLOAK_URL")
    realm = os.environ.get("KEYCLOAK_REALM")
    client_id = os.environ.get("KEYCLOAK_CLIENT_ID")
    client_secret = os.environ.get("KEYCLOAK_CLIENT_SECRET")

    if not all([url, realm, client_id]):
        raise RuntimeError(
            "Missing Keycloak configuration in environment. Set KEYCLOAK_URL, KEYCLOAK_REALM, KEYCLOAK_CLIENT_ID"
        )

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
async def lifespan(app: FastAPI):
    """Inicializa dependencias y registra handlers del Mediator durante el ciclo de vida de la app."""
    adapter = build_adapter_from_env()
    app.state.adapter = adapter

    app.state.create_handler = CreateUserHandler(adapter)
    app.state.update_handler = UpdateUserHandler(adapter)
    app.state.find_handler = FindUserByIdHandler(adapter)
    app.state.login_handler = LoginHandler(adapter)
    app.state.refresh_handler = RefreshTokenHandler(adapter)

    # Registra handlers del Mediator delegando a instancias creadas en app.state.
    @Mediator.handler
    def _create_handler_fn(request: CreateUserCommand):
        return app.state.create_handler.handle(request)

    @Mediator.handler
    def _update_handler_fn(request: UpdateUserCommand):
        return app.state.update_handler.handle(request)

    @Mediator.handler
    def _find_handler_fn(request: FindUserByIdQuery):
        return app.state.find_handler.handle(request)

    @Mediator.handler
    def _login_handler_fn(request: LoginCommand):
        return app.state.login_handler.handle(request)

    @Mediator.handler
    def _refresh_handler_fn(request: RefreshTokenCommand):
        return app.state.refresh_handler.handle(request)

    yield

# Configuración principal de FastAPI.
app = FastAPI(title="Users - Keycloak Adapter API", lifespan=lifespan)
app.add_middleware(DomainExceptionMiddleware)

# Expone endpoints de usuarios y autenticación.
app.include_router(users_router)
