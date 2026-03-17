import pytest

from Users_API import program as users_program


def test_build_adapter_reads_keycloak_from_vault(monkeypatch):
    monkeypatch.setenv("VAULT_KEYCLOAK_SECRET_PATH", "external/systemcctv/qa/keycloak")
    monkeypatch.setenv("VAULT_KV_MOUNT", "Desarrollo")
    monkeypatch.setattr(
        users_program,
        "read_secret_with_bootstrap",
        lambda path, mount_point: {
            "KEYCLOAK_URL": "https://kc.vault.local",
            "KEYCLOAK_REALM": "vault-realm",
            "KEYCLOAK_CLIENT_ID": "vault-client",
            "KEYCLOAK_CLIENT_SECRET": "vault-secret",
        },
    )

    adapter = users_program.build_adapter_from_vault()

    assert adapter.base_url == "https://kc.vault.local"
    assert adapter.realm == "vault-realm"
    assert adapter.client_id == "vault-client"
    assert adapter.client_secret == "vault-secret"


def test_build_adapter_raises_when_vault_path_is_missing(monkeypatch):
    monkeypatch.delenv("VAULT_KEYCLOAK_SECRET_PATH", raising=False)
    monkeypatch.delenv("VAULT_AUTH_SECRET_PATH", raising=False)

    with pytest.raises(RuntimeError, match="VAULT_KEYCLOAK_SECRET_PATH"):
        users_program.build_adapter_from_vault()


def test_build_adapter_raises_when_vault_is_configured_but_unreachable(monkeypatch):
    monkeypatch.setenv("VAULT_KEYCLOAK_SECRET_PATH", "external/systemcctv/qa/keycloak")
    monkeypatch.setattr(users_program, "read_secret_with_bootstrap", lambda path, mount_point: None)

    with pytest.raises(RuntimeError, match="Unable to read Keycloak secret from HashiVault"):
        users_program.build_adapter_from_vault()
