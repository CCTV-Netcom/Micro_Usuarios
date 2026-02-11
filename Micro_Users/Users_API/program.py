import os
from dotenv import load_dotenv
from pathlib import Path
from contextlib import asynccontextmanager

from fastapi import FastAPI
from mediatr import Mediator

from Users_Infraestruture.keycloak_adapter import KeycloakAdapter
from Users_Aplication.Handlers.Commands.CreateUserHandler import CreateUserHandler
from Users_Aplication.Handlers.Commands.UpdateUserHandler import UpdateUserHandler
from Users_Aplication.Handlers.Commands.LoginHandler import LoginHandler
from Users_Aplication.Handlers.Commands.RefreshTokenHandler import RefreshTokenHandler
from Users_Aplication.Handlers.Queries.FindUserByIDHandler import FindUserByIdHandler
from Users_Aplication.Commands.CreateUserCommand import CreateUserCommand
from Users_Aplication.Commands.UpdateUserCommand import UpdateUserCommand
from Users_Aplication.Commands.LoginCommand import LoginCommand
from Users_Aplication.Commands.RefreshTokenCommand import RefreshTokenCommand
from Users_Aplication.Queries.FindUserByIDQuerie import FindUserByIdQuery

from .middleware import DomainExceptionMiddleware
from .Controllers.controller import router as users_router


#Carga las variables de entorno desde el archivo .env ubicado en la raíz del proyecto (Micro_Users/.env)
env_path = Path(__file__).resolve().parent.parent / ".env"
if env_path.exists():
    load_dotenv(env_path)
#este archivo se encarga de configurar la app, usa el patron singlenton para crear una instancia de Keycloak y los handlers
# y los registra en el Mediator para que puedan ser usados en los controladores (routers)

def build_adapter_from_env() -> KeycloakAdapter:
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
    
    #Crea un app.state para almacenar la instancia del adaptador y los handlers, esto permite que sean 
    # compartidos entre las peticiones sin necesidad de crear una nueva instancia cada vez
    adapter = build_adapter_from_env()
    app.state.adapter = adapter

    app.state.create_handler = CreateUserHandler(adapter)
    app.state.update_handler = UpdateUserHandler(adapter)
    app.state.find_handler = FindUserByIdHandler(adapter)
    app.state.login_handler = LoginHandler(adapter)
    app.state.refresh_handler = RefreshTokenHandler(adapter)

    # Register Mediator handlers that delegate to the created handler instances
    # Se registra cada handler en el Mediator
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

#Se configura fastapi y se le asignan el titulo y el lifespan y se agrega el middleware para manejar las excepciones
app = FastAPI(title="Users - Keycloak Adapter API", lifespan=lifespan)
app.add_middleware(DomainExceptionMiddleware)

# Incluye el router de usuarios en la app, esto hace que las rutas (los endpoints) definidos en el router estén disponibles en la app
app.include_router(users_router)
