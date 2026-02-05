import base64
import io
import json
from pathlib import Path
import requests
from typing import Optional, Dict, Any
import pyotp
import qrcode
from Users_Aplication.Interfaces.i_keycloak import IKeycloakService
from Users_Domain.Exceptions.exceptions import (
    UserNotFoundException,
    InvalidCredentialsException,
    InvalidEmailFormatException,
    EmailAlreadyExistsException,
)
#Esta es la implementacion concreta de la interfaz IKeycloakService
#Aca se usan excepciones personalizadas del dominio de usuarios

class KeycloakAdapter(IKeycloakService):
    def __init__(
        self,
        base_url: str,
        realm: str,
        client_id: str = "",
        client_secret: Optional[str] = None,
        admin_user: Optional[str] = None,
        admin_password: Optional[str] = None,
    ) -> None:
        self.base_url = base_url.rstrip("/")
        self.realm = realm
        self.client_id = client_id
        self.client_secret = client_secret
        self.admin_user = admin_user
        self.admin_password = admin_password
        # Do not persist TOTP secrets on server by default. The generated secret
        # will be returned to the client and verification must include it.
        self._totp_secrets: Dict[str, str] = {}

    def _load_totp_cache(self) -> Dict[str, str]:
        # persistence disabled in this configuration
        return {}

    def _save_totp_cache(self) -> None:
        # no-op: persistence disabled
        return

    def _token_url(self) -> str:
        return f"{self.base_url}/realms/{self.realm}/protocol/openid-connect/token"

    def _admin_base(self) -> str:
        return f"{self.base_url}/admin/realms/{self.realm}"

    def _get_admin_token(self) -> str:
        if self.client_id and self.client_secret:
            data = {
                "grant_type": "client_credentials",
                "client_id": self.client_id,
                "client_secret": self.client_secret,
            }
            r = requests.post(self._token_url(), data=data, timeout=10)
            if r.ok:
                token = r.json().get("access_token")
                if token:
                    return token
                raise InvalidCredentialsException("Failed to obtain access token with client credentials")

        if self.admin_user and self.admin_password:
            data = {
                "grant_type": "password",
                "client_id": self.client_id or "admin-cli",
                "username": self.admin_user,
                "password": self.admin_password,
            }
            r = requests.post(self._token_url(), data=data, timeout=10)
            r.raise_for_status()
            token = r.json().get("access_token")
            if token:
                return token
            raise InvalidCredentialsException("Failed to obtain admin access token with provided credentials")
        raise InvalidCredentialsException("No admin credentials available")
    #Metodo de crear usuario
    def create_user(
        self,
        username: str,
        email: Optional[str] = None,
        firstName: Optional[str] = None,
        lastName: Optional[str] = None,
        password: Optional[str] = None,
        attributes: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        token = self._get_admin_token()
        url = f"{self._admin_base()}/users"
        # Ensure username is the same as email when email is provided
        if not email:
            raise InvalidEmailFormatException("email is required and will be used as username")
        # force username to be the email for consistency
        username = str(email)
        payload = {"username": username, "email": email, "enabled": True}
        if firstName:
            payload["firstName"] = firstName
        if lastName:
            payload["lastName"] = lastName
        # include attributes if provided (Keycloak expects attribute values as lists)
        if attributes:
            attrs_payload: Dict[str, Any] = {}
            for k, v in attributes.items():
                if isinstance(v, list):
                    attrs_payload[k] = [str(x) for x in v]
                else:
                    attrs_payload[k] = [str(v)]
            payload["attributes"] = attrs_payload

        headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
        r = requests.post(url, json=payload, headers=headers, timeout=10)
        if r.status_code == 409:
            raise EmailAlreadyExistsException(f"Email already exists: {r.text}")
        if r.status_code not in (201, 204):
            raise RuntimeError(f"Error creating user: {r.status_code} {r.text}")

        location = r.headers.get("Location")
        user_id = None
        if location:
            user_id = location.rstrip("/").split("/")[-1]

        if not user_id:
            found = self.find_user_by_username(username)
            user_id = found.get("id") if found else None

        if password and user_id:
            self.set_password(user_id, password, temporary=False)

        return {"id": user_id, "username": username}

    def set_password(self, user_id: str, new_password: str, temporary: bool = False) -> None:
        token = self._get_admin_token()
        url = f"{self._admin_base()}/users/{user_id}/reset-password"
        payload = {"type": "password", "value": new_password, "temporary": temporary}
        headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
        r = requests.put(url, json=payload, headers=headers, timeout=10)
        r.raise_for_status()

    def find_user_by_id(self, user_id: str) -> Optional[Dict[str, Any]]:
        token = self._get_admin_token()
        url = f"{self._admin_base()}/users/{user_id}"   
        headers = {"Authorization": f"Bearer {token}"}
        r = requests.get(url, headers=headers, timeout=10)
        try:
            r.raise_for_status()
        except requests.exceptions.HTTPError as e:
            if r.status_code == 404:
                raise UserNotFoundException(f"User with id {user_id} not found") from e
            raise
        data = r.json()
        # Keycloak returns a single user object for GET /users/{id}.
        # Some code may assume a list; handle both dict and list safely.
        if not data:
            raise UserNotFoundException(f"User with id {user_id} not found")
        if isinstance(data, list):
            return data[0] if data else None
        return data


    def update_user(self, user_id: str, data: Dict[str, Any]) -> None:
        token = self._get_admin_token()
        url = f"{self._admin_base()}/users/{user_id}"
        headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
        r = requests.put(url, json=data, headers=headers, timeout=10)
        if not r.ok:
            raise RuntimeError(f"Error updating user: {r.status_code} {r.text}")

    def login(self, username: str, password: str, totp: Optional[str] = None) -> Dict[str, Any]:
        data = {"grant_type": "password", "client_id": self.client_id, "username": username, "password": password}
        if totp:
            data["totp"] = totp
        if self.client_secret:
            data["client_secret"] = self.client_secret
        r = requests.post(self._token_url(), data=data, timeout=10)
        r.raise_for_status()
        return r.json()

    def refresh_token(self, refresh_token: str) -> Dict[str, Any]:
        data = {"grant_type": "refresh_token", "refresh_token": refresh_token}
        if self.client_id:
            data["client_id"] = self.client_id
        if self.client_secret:
            data["client_secret"] = self.client_secret
        r = requests.post(self._token_url(), data=data, timeout=10)
        r.raise_for_status()
        return r.json()

    def change_password(self, user_id: str, new_password: str, temporary: bool = False) -> None:
        self.set_password(user_id, new_password, temporary=temporary)

    def register_totp_device(self, user_id: str, device_name: Optional[str] = None) -> Dict[str, Any]:
        existing = self.find_user_by_id(user_id)
        required_actions = list(existing.get("requiredActions") or [])
        if "CONFIGURE_TOTP" not in required_actions:
            required_actions.append("CONFIGURE_TOTP")

        attributes = dict(existing.get("attributes") or {})
        if device_name:
            attributes["otpDevice"] = [str(device_name)]

        # Generate TOTP secret and QR (secret returned to client; not persisted)
        secret = pyotp.random_base32()
        issuer = self.realm
        account = existing.get("email") or existing.get("username") or user_id
        otp = pyotp.TOTP(secret)
        otpauth_url = otp.provisioning_uri(name=account, issuer_name=issuer)

        qr = qrcode.QRCode(box_size=6, border=2)
        qr.add_data(otpauth_url)
        qr.make(fit=True)
        img = qr.make_image(fill_color="black", back_color="white")
        buffer = io.BytesIO()
        img.save(buffer, format="PNG")
        qr_base64 = base64.b64encode(buffer.getvalue()).decode("utf-8")

        # try to register the credential in Keycloak
        configured = False
        try:
            credential_data = {"subType": "totp", "digits": 6, "period": 30, "algorithm": "HmacSHA1"}
            secret_data = {"value": secret}
            cred_payload = {
                "type": "otp",
                "temporary": False,
                "userLabel": device_name or "Authenticator",
                "credentialData": credential_data,
                "secretData": secret_data,
            }
            token = self._get_admin_token()
            url = f"{self._admin_base()}/users/{user_id}/credentials"
            headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
            r = requests.post(url, json=cred_payload, headers=headers, timeout=10)
            if r.status_code in (200, 201, 204):
                configured = True
            else:
                # attach response for debugging
                configured = False
                # try to include response text in attributes for debugging
                attributes["_last_credential_error"] = [r.text]
        except Exception as e:
            configured = False
            attributes["_last_credential_error"] = [str(e)]

        # Do NOT persist the secret in user attributes or on disk.
        payload: Dict[str, Any] = {"requiredActions": required_actions, "attributes": attributes}
        # Include required fields to satisfy realm validation rules (e.g., email required)
        if existing.get("email"):
            payload["email"] = existing.get("email")
        if existing.get("username"):
            payload["username"] = existing.get("username")
        if existing.get("firstName"):
            payload["firstName"] = existing.get("firstName")
        if existing.get("lastName"):
            payload["lastName"] = existing.get("lastName")
        self.update_user(user_id, payload)

        return {
            "user_id": user_id,
            "required_action": "CONFIGURE_TOTP",
            "device_name": device_name,
            "secret": secret,
            "otpauth_url": otpauth_url,
            "qr_code_base64": qr_base64,
            "configured": configured,
        }

    def get_cached_totp_secret(self, user_id: str) -> Optional[str]:
        # Cache not used when persistence is disabled
        return None

    def verify_totp(self, user_id: str, code: str, secret: Optional[str] = None) -> Dict[str, Any]:
        existing = self.find_user_by_id(user_id)
        attrs = dict(existing.get("attributes") or {})

        # Prefer explicit secret provided by client (server does not persist it)
        if not secret:
            for key in ("otpSecret", "otpsecret", "otp_secret", "otp"):
                if key in attrs:
                    val = attrs.get(key)
                    if isinstance(val, list) and len(val) > 0:
                        secret = val[0]
                    elif isinstance(val, str):
                        secret = val
                    break
        if not secret:
            return {"success": False, "message": "TOTP secret not provided"}

        # Normalize code (strip spaces) and validate format
        code = "".join(str(code).split())
        if not code.isdigit():
            return {"success": False, "message": "TOTP code must be numeric"}
        if len(code) not in (6, 8):
            return {"success": False, "message": "TOTP code length invalid"}

        try:
            otp = pyotp.TOTP(secret)
            ok = otp.verify(code, valid_window=2)
        except Exception as e:
            return {"success": False, "message": f"Verification error: {e}"}

        if not ok:
            return {"success": False, "message": "Invalid TOTP code"}

        # On success: remove CONFIGURE_TOTP from requiredActions if present
        required_actions = list(existing.get("requiredActions") or [])
        if "CONFIGURE_TOTP" in required_actions:
            required_actions = [a for a in required_actions if a != "CONFIGURE_TOTP"]

        # mark configured attribute
        attrs["otpConfigured"] = ["true"]

        payload = {"requiredActions": required_actions, "attributes": attrs}
        # include mandatory fields to satisfy validation
        if existing.get("email"):
            payload["email"] = existing.get("email")
        if existing.get("username"):
            payload["username"] = existing.get("username")

        self.update_user(user_id, payload)

        # Optional: remove secret after verification for safety
        if user_id in self._totp_secrets:
            self._totp_secrets.pop(user_id, None)
            self._save_totp_cache()

        return {"success": True, "message": "TOTP verified and device configured"}
