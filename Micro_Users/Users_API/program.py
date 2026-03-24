import os
from pathlib import Path
from contextlib import asynccontextmanager

from fastapi import FastAPI
from mediatr import Mediator

from Users_Infrastruture.keycloak_adapter import KeycloakAdapter
from Users_Infrastruture.runtime_network import normalize_local_url_for_container
from Users_Infrastruture.Vault.vault_client import read_secret_with_bootstrap
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


# NOTE: environment variables are provided externally (no .env loading here).
#este archivo se encarga de configurar la app, usa el patron singlenton para crear una instancia de Keycloak y los handlers
# y los registra en el Mediator para que puedan ser usados en los controladores (routers)


def _first_present(secret: dict[str, str], *keys: str) -> str | None:
    for key in keys:
        value = secret.get(key)
        if value:
            return str(value)
    return None


def _get_keycloak_config_from_vault() -> dict[str, str]:
    vault_path = os.environ.get("VAULT_KEYCLOAK_SECRET_PATH") or os.environ.get("VAULT_AUTH_SECRET_PATH")
    if not vault_path:
        raise RuntimeError(
            "Missing Vault path for Keycloak. Set VAULT_KEYCLOAK_SECRET_PATH"
        )

    vault_mount = os.environ.get("VAULT_KEYCLOAK_KV_MOUNT") or os.environ.get("VAULT_KV_MOUNT")
    secret = read_secret_with_bootstrap(path=vault_path, mount_point=vault_mount)
    if not secret:
        raise RuntimeError(
            "Unable to read Keycloak secret from HashiVault. "
            "Verify VAULT_ADDR, ROLE_ID/SECRET_ID, VAULT_KV_MOUNT and VAULT_KEYCLOAK_SECRET_PATH"
        )

    return {
        "KEYCLOAK_URL": normalize_local_url_for_container(
            _first_present(secret, "KEYCLOAK_URL", "keycloak_url", "url", "base_url") or ""
        ),
        "KEYCLOAK_REALM": _first_present(secret, "KEYCLOAK_REALM", "keycloak_realm", "realm") or "",
        "KEYCLOAK_CLIENT_ID": _first_present(secret, "KEYCLOAK_CLIENT_ID", "keycloak_client_id", "client_id") or "",
        "KEYCLOAK_CLIENT_SECRET": _first_present(secret, "KEYCLOAK_CLIENT_SECRET", "keycloak_client_secret", "client_secret") or "",
    }


def build_adapter_from_vault() -> KeycloakAdapter:
    """Construye el adaptador de Keycloak a partir de configuracion obtenida desde Vault."""
    config = _get_keycloak_config_from_vault()

    url = config["KEYCLOAK_URL"]
    realm = config["KEYCLOAK_REALM"]
    client_id = config["KEYCLOAK_CLIENT_ID"]
    client_secret = config["KEYCLOAK_CLIENT_SECRET"]

    if not all([url, realm, client_id]):
        raise RuntimeError(
            "Vault secret incomplete for Keycloak. "
            "Missing one of: KEYCLOAK_URL, KEYCLOAK_REALM, KEYCLOAK_CLIENT_ID"
        )

    if not client_secret:
        raise RuntimeError(
            "Vault secret incomplete for Keycloak. Missing KEYCLOAK_CLIENT_SECRET"
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
    adapter = build_adapter_from_vault()
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
