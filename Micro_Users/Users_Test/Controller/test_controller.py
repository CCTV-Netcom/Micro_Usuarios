import pytest
from fastapi.testclient import TestClient

from Users_API import main as users_main
from Users_Aplication.DTOs.UserDTO import UserDTO
from Users_Aplication.DTOs.TokenDTO import TokenDTO
from Users_Aplication.DTOs.AuthDTO import TotpRegisterResponseDTO, TotpVerifyResponseDTO
from Users_Domain.Exceptions.exceptions import UserNotFoundException


class FakeAdapter:
    def __init__(self):
        self.realm = "test-realm"
        self._totp_secrets = {}

    def find_user_by_id(self, user_id: str):
        if user_id == "missing":
            raise UserNotFoundException("User not found")
        if user_id == "nosecret":
            return {
                "id": user_id,
                "username": "user",
                "email": "user@example.com",
                "attributes": {},
            }
        return {
            "id": user_id,
            "username": "user",
            "email": "user@example.com",
            "attributes": {"otpSecret": ["ABC123"]},
        }

    def get_cached_totp_secret(self, user_id: str):
        return self._totp_secrets.get(user_id)

# pytest fixture para crear un cliente de prueba con el adaptador simulado
#En este caso lo usamos para llamar a los endpoints de la API y verificar que las respuestas sean correctas, sin necesidad de depender de una implementación real del adaptador o de la base de datos.

@pytest.fixture()
def client(monkeypatch):
    monkeypatch.setattr(users_main, "build_adapter_from_env", lambda: FakeAdapter())
    with TestClient(users_main.app) as test_client:
        yield test_client


def test_create_user_ok(client, monkeypatch):
    user_dto = UserDTO(
        id="u-1",
        username="user@example.com",
        email="user@example.com",
        first_name="User",
        last_name="Test",
        attributes={"Cedula": ["123"]},
    )
    monkeypatch.setattr(users_main.Mediator, "send", lambda cmd: user_dto)

    response = client.post(
        "/users",
        data={
            "password": "secret",
            "email": "user@example.com",
            "first_name": "User",
            "last_name": "Test",
            "cedula": 123,
        },
    )

    assert response.status_code == 200
    assert response.json()["id"] == "u-1"
    assert response.json()["email"] == "user@example.com"



def test_create_user_cedula_not_int(client):
    
    response = client.post(
        "/users",
        data={
            "password": "secret",
            "email": "user@example.com",
            "first_name": "User",
            "last_name": "Test",
            "cedula": "V-23320983",
        },
    )
    assert response.status_code == 422
    detail = response.json()["detail"][0]
    assert detail["loc"] == ["body", "cedula"]
    assert "value is not a valid integer" in detail["msg"]

            
def test_update_user_ok(client, monkeypatch):
    user_dto = UserDTO(
        id="u-2",
        username="user2@example.com",
        email="user2@example.com",
        first_name="New",
        last_name="Name",
        attributes=None,
    )
    monkeypatch.setattr(users_main.Mediator, "send", lambda cmd: user_dto)

    response = client.put(
        "/users/u-2",
        json={"first_name": "New", "last_name": "Name"},
    )

    assert response.status_code == 200
    assert response.json()["id"] == "u-2"
    assert response.json()["first_name"] == "New"


def test_find_user_not_found(client, monkeypatch):
    monkeypatch.setattr(users_main.Mediator, "send", lambda cmd: None)

    response = client.get("/users/u-404")

    assert response.status_code == 404
    assert response.json()["detail"] == "User not found"


def test_login_ok(client, monkeypatch):
    token_dto = TokenDTO(access_token="access", refresh_token="refresh")
    monkeypatch.setattr(users_main.Mediator, "send", lambda cmd: token_dto)

    response = client.post(
        "/auth/login",
        json={"username": "user@example.com", "password": "secret"},
    )

    assert response.status_code == 200
    assert response.json()["access_token"] == "access"


def test_login_invalid_credentials(client, monkeypatch):
    def _raise(cmd):
        raise Exception("invalid")

    monkeypatch.setattr(users_main.Mediator, "send", _raise)

    response = client.post(
        "/auth/login",
        json={"username": "user@example.com", "password": "bad"},
    )

    assert response.status_code == 401
    assert response.json()["detail"] == "Invalid credentials"


def test_refresh_token_ok(client, monkeypatch):
    token_dto = TokenDTO(access_token="access2", refresh_token="refresh2")
    monkeypatch.setattr(users_main.Mediator, "send", lambda cmd: token_dto)

    response = client.post(
        "/auth/refresh",
        json={"refresh_token": "refresh2"},
    )

    assert response.status_code == 200
    assert response.json()["access_token"] == "access2"


def test_register_totp_ok(client, monkeypatch):
    totp_dto = TotpRegisterResponseDTO(
        user_id="u-3",
        required_action="CONFIGURE_TOTP",
        device_name="Phone",
        secret="SECRET",
        otpauth_url="otpauth://totp/test",
        configured=False,
    )
    monkeypatch.setattr(users_main.Mediator, "send", lambda cmd: totp_dto)

    response = client.post(
        "/users/u-3/totp/register",
        json={"device_name": "Phone"},
    )

    assert response.status_code == 200
    assert response.json()["user_id"] == "u-3"
    assert response.json()["qr_code_url"] == "/users/u-3/totp/qr"


def test_verify_totp_error(client, monkeypatch):
    def _raise(cmd):
        raise Exception("fail")

    monkeypatch.setattr(users_main.Mediator, "send", _raise)

    response = client.post(
        "/users/u-3/totp/verify",
        json={"code": "123456", "secret": "SECRET"},
    )

    assert response.status_code == 400
    assert "TOTP verification failed" in response.json()["detail"]


def test_totp_qr_image(client):
    response = client.get("/users/u-3/totp/qr")

    assert response.status_code == 200
    assert response.headers["content-type"].startswith("image/png")
    assert len(response.content) > 0


def test_totp_qr_secret_not_found(client):
    response = client.get("/users/nosecret/totp/qr")

    assert response.status_code == 404
    assert response.json()["detail"] == "TOTP secret not found"
