import pytest
from fastapi.testclient import TestClient

from Users_API import program as users_program
from Users_Application.DTOs.TokenDTO import TokenDTO
from Users_Application.DTOs.UserDTO import UserDTO


class FakeAdapter:
    def __init__(self):
        self.realm = "test-realm"

    def validate_token(self, token: str):
        if token == "valid-token":
            return {"active": True, "sub": "u-1"}
        return None


@pytest.fixture()
def client(monkeypatch):
    monkeypatch.setattr(users_program, "build_adapter_from_env", lambda: FakeAdapter())
    with TestClient(users_program.app) as test_client:
        yield test_client


def test_create_user_ok(client, monkeypatch):
    user_dto = UserDTO(
        id="u-1",
        username="user@example.com",
        email="user@example.com",
        first_name="User",
        last_name="Test",
        rol="Operador",
        attributes={"Cedula": ["12345678"]},
    )
    monkeypatch.setattr(users_program.Mediator, "send", lambda _: user_dto)

    response = client.post(
        "/users",
        data={
            "password": "Password123!",
            "email": "user@example.com",
            "first_name": "User",
            "last_name": "Test",
            "cedula": 12345678,
            "rol": "Operador",
        },
    )

    assert response.status_code == 200
    assert response.json()["id"] == "u-1"
    assert response.json()["email"] == "user@example.com"


def test_create_user_failure(client, monkeypatch):
    monkeypatch.setattr(users_program.Mediator, "send", lambda _: None)

    response = client.post(
        "/users",
        data={
            "password": "Password123!",
            "email": "user@example.com",
            "first_name": "User",
            "last_name": "Test",
            "cedula": 12345678,
            "rol": "Operador",
        },
    )

    assert response.status_code == 500
    assert response.json()["detail"] == "Failed to create user"


def test_update_user_ok(client, monkeypatch):
    user_dto = UserDTO(
        id="u-2",
        username="user2@example.com",
        email="user2@example.com",
        first_name="New",
        last_name="Name",
        rol="Administrador",
        attributes=None,
    )
    monkeypatch.setattr(users_program.Mediator, "send", lambda _: user_dto)

    response = client.put(
        "/users/u-2",
        json={"first_name": "New", "last_name": "Name"},
    )

    assert response.status_code == 200
    assert response.json()["id"] == "u-2"
    assert response.json()["first_name"] == "New"


def test_update_user_not_found(client, monkeypatch):
    monkeypatch.setattr(users_program.Mediator, "send", lambda _: None)

    response = client.put(
        "/users/u-404",
        json={"first_name": "Missing", "last_name": "User"},
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "User not found or update failed"


def test_find_user_not_found(client, monkeypatch):
    monkeypatch.setattr(users_program.Mediator, "send", lambda _: None)

    response = client.get("/users/u-404")

    assert response.status_code == 404
    assert response.json()["detail"] == "User not found"


def test_find_user_ok(client, monkeypatch):
    user_dto = UserDTO(
        id="u-10",
        username="find@example.com",
        email="find@example.com",
        first_name="Find",
        last_name="User",
        rol="Operador",
        attributes=None,
    )
    monkeypatch.setattr(users_program.Mediator, "send", lambda _: user_dto)

    response = client.get("/users/u-10")

    assert response.status_code == 200
    assert response.json()["id"] == "u-10"


def test_login_ok(client, monkeypatch):
    token_dto = TokenDTO(access_token="access", refresh_token="refresh")
    monkeypatch.setattr(users_program.Mediator, "send", lambda _: token_dto)

    response = client.post(
        "/auth/login",
        json={"username": "user@example.com", "password": "Password123!"},
    )

    assert response.status_code == 200
    assert response.json()["access_token"] == "access"


def test_login_invalid_credentials(client, monkeypatch):
    def _raise(_):
        raise Exception("invalid")

    monkeypatch.setattr(users_program.Mediator, "send", _raise)

    response = client.post(
        "/auth/login",
        json={"username": "user@example.com", "password": "bad"},
    )

    assert response.status_code == 401
    assert response.json()["detail"] == "Invalid credentials"


def test_refresh_token_ok(client, monkeypatch):
    token_dto = TokenDTO(access_token="access2", refresh_token="refresh2")
    monkeypatch.setattr(users_program.Mediator, "send", lambda _: token_dto)

    response = client.post(
        "/auth/refresh",
        json={"refresh_token": "refresh2"},
    )

    assert response.status_code == 200
    assert response.json()["access_token"] == "access2"


def test_refresh_token_invalid(client, monkeypatch):
    def _raise(_):
        raise Exception("invalid refresh")

    monkeypatch.setattr(users_program.Mediator, "send", _raise)

    response = client.post(
        "/auth/refresh",
        json={"refresh_token": "bad"},
    )

    assert response.status_code == 401
    assert response.json()["detail"] == "Invalid refresh token"


def test_validate_token_ok_from_authorization_header(client):
    response = client.get("/auth/validate", headers={"Authorization": "Bearer valid-token"})
    assert response.status_code == 204


def test_validate_token_missing(client):
    response = client.get("/auth/validate")
    assert response.status_code == 401
    assert response.json()["detail"] == "Missing token"


def test_validate_token_invalid(client):
    response = client.get("/auth/validate", headers={"Authorization": "Bearer invalid-token"})
    assert response.status_code == 401
    assert response.json()["detail"] == "Invalid token"
