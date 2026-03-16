import os
from pathlib import Path
from typing import Optional, Dict

from dotenv import load_dotenv

from Users_Infrastruture.runtime_network import normalize_local_url_for_container

load_dotenv(Path(__file__).resolve().parents[2] / ".env")


class VaultClient:
    def __init__(
        self,
        vault_addr: Optional[str] = None,
        role_id: Optional[str] = None,
        secret_id: Optional[str] = None,
        mount_point: Optional[str] = None,
    ) -> None:
        try:
            import hvac
        except Exception as exc:
            raise RuntimeError("hvac is required to use VaultClient") from exc

        vault_addr = normalize_local_url_for_container(vault_addr or os.getenv("VAULT_ADDR", ""))
        role_id = role_id or os.getenv("ROLE_ID") or os.getenv("VAULT_ROLE_ID")
        secret_id = secret_id or os.getenv("SECRET_ID") or os.getenv("VAULT_SECRET_ID")
        self._mount_point = (
            mount_point
            or os.getenv("VAULT_KV_MOUNT")
            or os.getenv("VAULT_MOUNT_POINT")
            or "secret"
        )

        if not vault_addr:
            raise RuntimeError("Vault address not configured")

        if not (role_id and secret_id):
            raise RuntimeError("Vault AppRole not configured (ROLE_ID/SECRET_ID)")

        self._client = hvac.Client(url=vault_addr)
        self._client.auth.approle.login(role_id=role_id, secret_id=secret_id)

        if not self._client.is_authenticated():
            raise RuntimeError("Vault authentication failed")

    def read_secret(self, path: str) -> Optional[Dict[str, str]]:
        try:
            result = self._client.secrets.kv.v2.read_secret_version(
                path=path, mount_point=self._mount_point
            )
        except Exception:
            return None

        data = result.get("data", {}).get("data", {}) if result else {}
        return data or None

    def write_secret(self, path: str, secret: Dict[str, str]) -> None:
        self._client.secrets.kv.v2.create_or_update_secret(
            path=path, mount_point=self._mount_point, secret=secret
        )

    def delete_secret(self, path: str) -> None:
        self._client.secrets.kv.v2.delete_metadata_and_all_versions(
            path=path, mount_point=self._mount_point
        )


def read_secret_with_bootstrap(
    path: str,
    mount_point: Optional[str] = None,
) -> Optional[Dict[str, str]]:
    try:
        client = VaultClient(mount_point=mount_point)
        return client.read_secret(path)
    except Exception:
        return None
