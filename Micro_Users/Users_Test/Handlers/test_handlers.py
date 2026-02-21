import pytest
from pydantic import ValidationError

from Users_Application.Commands.CreateUserCommand import CreateUserCommand
from Users_Application.Commands.LoginCommand import LoginCommand
from Users_Application.Commands.RefreshTokenCommand import RefreshTokenCommand
from Users_Application.Commands.UpdateUserCommand import UpdateUserCommand
from Users_Application.Handlers.Commands.CreateUserHandler import CreateUserHandler
from Users_Application.Handlers.Commands.LoginHandler import LoginHandler
from Users_Application.Handlers.Commands.RefreshTokenHandler import RefreshTokenHandler
from Users_Application.Handlers.Commands.UpdateUserHandler import UpdateUserHandler
from Users_Application.Handlers.Queries.FindUserByIDHandler import FindUserByIdHandler
from Users_Application.Queries.FindUserByIDQuerie import FindUserByIdQuery
from Users_Domain.Enums.role import RoleEnum
from Users_Domain.Exceptions.exceptions import UserNotFoundException


class FakeKeycloakService:
    def __init__(self):
        self.updated_payload = None
        self.assigned_role = None

    def create_user(self, **kwargs):
        return {"id": "user-id-1", "username": kwargs.get("username")}

    def find_user_by_id(self, user_id: str):
        if user_id == "missing":
            raise UserNotFoundException("not found")
        return {
            "id": user_id,
            "username": "user@example.com",
            "email": "user@example.com",
            "firstName": "User",
            "lastName": "Test",
            "realmRoles": [RoleEnum.OPERADOR.value],
            "attributes": {"Cedula": ["12345678"]},
        }

    def update_user(self, user_id: str, data):
        self.updated_payload = (user_id, data)

    def login(self, username: str, password: str):
        return {"access_token": "access", "refresh_token": "refresh"}

    def refresh_token(self, refresh_token: str):
        return {"access_token": "access2", "refresh_token": "refresh2"}

    def change_password(self, user_id: str, new_password: str, temporary: bool = False):
        return None

    def assign_realm_role(self, user_id: str, role_name: str):
        self.assigned_role = (user_id, role_name)


class FakeCreateWithoutUserInfo(FakeKeycloakService):
    def find_user_by_id(self, user_id: str):
        raise RuntimeError("temporary keycloak issue")


class FakeEmptyUserInfo(FakeKeycloakService):
    def find_user_by_id(self, user_id: str):
        return None


def test_create_user_handler_ok():
    service = FakeKeycloakService()
    handler = CreateUserHandler(service)

    command = CreateUserCommand(
        password="Password123!",
        email="user@example.com",
        first_name="User",
        last_name="Test",
        cedula=12345678,
        rol=RoleEnum.OPERADOR,
    )

    result = handler.handle(command)

    assert result is not None
    assert result.id == "user-id-1"
    assert result.email == "user@example.com"
    assert service.assigned_role == ("user-id-1", RoleEnum.OPERADOR.value)


def test_create_user_handler_returns_minimal_dto_when_lookup_fails():
    service = FakeCreateWithoutUserInfo()
    handler = CreateUserHandler(service)

    command = CreateUserCommand(
        password="Password123!",
        email="user@example.com",
        first_name="User",
        last_name="Test",
        cedula=12345678,
        rol=RoleEnum.OPERADOR,
    )

    result = handler.handle(command)

    assert result is not None
    assert result.id == "user-id-1"
    assert result.username == "user@example.com"


def test_create_user_handler_raises_validation_error_for_weak_password():
    service = FakeEmptyUserInfo()
    handler = CreateUserHandler(service)

    command = CreateUserCommand(
        password="weak",
        email="user@example.com",
        first_name="User",
        last_name="Test",
        cedula=12345678,
        rol=RoleEnum.OPERADOR,
    )

    with pytest.raises(ValidationError):
        handler.handle(command)


def test_update_user_handler_ok():
    service = FakeKeycloakService()
    handler = UpdateUserHandler(service)

    command = UpdateUserCommand(user_id="user-id-1", first_name="Nuevo", last_name="Nombre")
    result = handler.handle(command)

    assert result is not None
    assert result.id == "user-id-1"
    assert service.updated_payload == ("user-id-1", {"firstName": "Nuevo", "lastName": "Nombre"})


def test_login_handler_ok():
    service = FakeKeycloakService()
    handler = LoginHandler(service)

    result = handler.handle(LoginCommand(username="user@example.com", password="Password123!"))

    assert result.access_token == "access"
    assert result.refresh_token == "refresh"


def test_refresh_token_handler_ok():
    service = FakeKeycloakService()
    handler = RefreshTokenHandler(service)

    result = handler.handle(RefreshTokenCommand(refresh_token="refresh"))

    assert result.access_token == "access2"
    assert result.refresh_token == "refresh2"


def test_find_user_handler_ok():
    service = FakeKeycloakService()
    handler = FindUserByIdHandler(service)

    result = handler.handle(FindUserByIdQuery(user_id="user-id-1"))

    assert result is not None
    assert result.id == "user-id-1"


def test_find_user_handler_returns_none_when_not_found():
    service = FakeKeycloakService()
    handler = FindUserByIdHandler(service)

    result = handler.handle(FindUserByIdQuery(user_id="missing"))

    assert result is None
