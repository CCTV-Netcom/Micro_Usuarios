import pytest
import requests

from Users_Domain.Exceptions.exceptions import (
    EmailAlreadyExistsException,
    InvalidCredentialsException,
    InvalidEmailFormatException,
    UserNotFoundException,
)
from Users_Infrastruture.keycloak_adapter import KeycloakAdapter


class FakeResponse:
    def __init__(self, status_code=200, payload=None, text="", headers=None):
        self.status_code = status_code
        self._payload = payload if payload is not None else {}
        self.text = text
        self.headers = headers or {}

    @property
    def ok(self):
        return 200 <= self.status_code < 300

    def json(self):
        return self._payload

    def raise_for_status(self):
        if not self.ok:
            raise requests.exceptions.HTTPError(f"status={self.status_code}")


@pytest.fixture()
def adapter():
    return KeycloakAdapter(
        base_url="http://keycloak.local",
        realm="test-realm",
        client_id="client-id",
        client_secret="client-secret",
    )


def test_get_admin_token_ok(monkeypatch, adapter):
    monkeypatch.setattr(
        requests,
        "post",
        lambda *args, **kwargs: FakeResponse(200, {"access_token": "admin-token"}),
    )

    token = adapter._get_admin_token()

    assert token == "admin-token"


def test_get_admin_token_requires_credentials():
    client = KeycloakAdapter(base_url="http://keycloak.local", realm="test")
    with pytest.raises(InvalidCredentialsException):
        client._get_admin_token()


def test_create_user_requires_email(monkeypatch, adapter):
    monkeypatch.setattr(adapter, "_get_admin_token", lambda: "admin-token")
    with pytest.raises(InvalidEmailFormatException):
        adapter.create_user(username="user")


def test_create_user_raises_conflict(monkeypatch, adapter):
    monkeypatch.setattr(adapter, "_get_admin_token", lambda: "admin-token")
    monkeypatch.setattr(
        requests,
        "post",
        lambda *args, **kwargs: FakeResponse(409, text="conflict"),
    )

    with pytest.raises(EmailAlreadyExistsException):
        adapter.create_user(username="u", email="user@example.com")


def test_create_user_sets_password_and_returns_id(monkeypatch, adapter):
    monkeypatch.setattr(adapter, "_get_admin_token", lambda: "admin-token")

    calls = {"set_password": False}

    def fake_post(*args, **kwargs):
        return FakeResponse(201, headers={"Location": "http://k/admin/realms/r/users/u-1"})

    def fake_set_password(user_id, new_password, temporary=False):
        calls["set_password"] = (user_id, new_password, temporary)

    monkeypatch.setattr(requests, "post", fake_post)
    monkeypatch.setattr(adapter, "set_password", fake_set_password)

    result = adapter.create_user(
        username="user@example.com",
        email="user@example.com",
        password="Password123!",
        attributes={"Cedula": 12345678},
    )

    assert result == {"id": "u-1", "username": "user@example.com"}
    assert calls["set_password"] == ("u-1", "Password123!", False)


def test_find_user_by_id_not_found(monkeypatch, adapter):
    monkeypatch.setattr(adapter, "_get_admin_token", lambda: "admin-token")
    monkeypatch.setattr(requests, "get", lambda *args, **kwargs: FakeResponse(404))

    with pytest.raises(UserNotFoundException):
        adapter.find_user_by_id("missing")


def test_find_user_by_id_includes_roles(monkeypatch, adapter):
    monkeypatch.setattr(adapter, "_get_admin_token", lambda: "admin-token")

    def fake_get(url, *args, **kwargs):
        if url.endswith("/role-mappings/realm"):
            return FakeResponse(200, [{"name": "Operador"}])
        return FakeResponse(200, {"id": "u-1", "username": "user@example.com"})

    monkeypatch.setattr(requests, "get", fake_get)

    result = adapter.find_user_by_id("u-1")

    assert result["id"] == "u-1"
    assert result["realmRoles"] == ["Operador"]


def test_update_user_not_found(monkeypatch, adapter):
    monkeypatch.setattr(adapter, "_get_admin_token", lambda: "admin-token")
    monkeypatch.setattr(requests, "put", lambda *args, **kwargs: FakeResponse(404))

    with pytest.raises(UserNotFoundException):
        adapter.update_user("missing", {"firstName": "Name"})


def test_login_ok(monkeypatch, adapter):
    monkeypatch.setattr(
        requests,
        "post",
        lambda *args, **kwargs: FakeResponse(200, {"access_token": "a", "refresh_token": "r"}),
    )

    result = adapter.login("user@example.com", "Password123!")

    assert result["access_token"] == "a"


def test_refresh_token_ok(monkeypatch, adapter):
    monkeypatch.setattr(
        requests,
        "post",
        lambda *args, **kwargs: FakeResponse(200, {"access_token": "a2", "refresh_token": "r2"}),
    )

    result = adapter.refresh_token("r")

    assert result["access_token"] == "a2"


def test_validate_token_userinfo_ok(monkeypatch, adapter):
    monkeypatch.setattr(requests, "get", lambda *args, **kwargs: FakeResponse(200, {"sub": "u-1"}))

    result = adapter.validate_token("token")

    assert result == {"sub": "u-1"}


def test_validate_token_uses_introspection_when_userinfo_fails(monkeypatch, adapter):
    def fake_get(*args, **kwargs):
        return FakeResponse(403, {"detail": "forbidden"})

    def fake_post(*args, **kwargs):
        return FakeResponse(200, {"active": True, "sub": "u-1"})

    monkeypatch.setattr(requests, "get", fake_get)
    monkeypatch.setattr(requests, "post", fake_post)

    result = adapter.validate_token("token")

    assert result == {"active": True, "sub": "u-1"}


def test_assign_realm_role_role_not_found(monkeypatch, adapter):
    monkeypatch.setattr(adapter, "_get_admin_token", lambda: "admin-token")

    def fake_get(*args, **kwargs):
        return FakeResponse(404)

    monkeypatch.setattr(requests, "get", fake_get)

    with pytest.raises(RuntimeError, match="Role not found"):
        adapter.assign_realm_role("u-1", "Operador")
