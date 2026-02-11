import requests
from typing import Optional, Dict, Any
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
    ) -> None:
        self.base_url = base_url.rstrip("/")
        self.realm = realm
        self.client_id = client_id
        self.client_secret = client_secret

    def _token_url(self) -> str:
        return f"{self.base_url}/realms/{self.realm}/protocol/openid-connect/token"

    def _admin_base(self) -> str:
        return f"{self.base_url}/admin/realms/{self.realm}"

    def _userinfo_url(self) -> str:
        return f"{self.base_url}/realms/{self.realm}/protocol/openid-connect/userinfo"

    def _realm_role_url(self, role_name: str) -> str:
        return f"{self._admin_base()}/roles/{role_name}"

    def _get_admin_token(self) -> str:
        if not (self.client_id and self.client_secret):
            raise InvalidCredentialsException("Client credentials required for admin operations")

        data = {
            "grant_type": "client_credentials",
            "client_id": self.client_id,
            "client_secret": self.client_secret,
        }
        response = requests.post(self._token_url(), data=data, timeout=10)
        if response.ok:
            token = response.json().get("access_token")
            if token:
                return token
            raise InvalidCredentialsException("Failed to obtain access token with client credentials")
        response.raise_for_status()
        raise InvalidCredentialsException("Failed to obtain access token with client credentials")
    
    
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
        
        
        # Se fuerza a que el username se igual al correo por consistencia con el dominio de usuarios, ya que el email es un identificador unico y se usara como username en Keycloak
        username = str(email)
        payload = {
            "username": username,
            "email": email,
            "enabled": True,
        }
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
        response = requests.post(url, json=payload, headers=headers, timeout=10)
        if response.status_code == 409:
            raise EmailAlreadyExistsException(f"Email already exists: {response.text}")
        if response.status_code not in (201, 204):
            raise RuntimeError(f"Error creating user: {response.status_code} {response.text}")

        location = response.headers.get("Location")
        user_id = None
        if location:
            user_id = location.rstrip("/").split("/")[-1]

        if not user_id:
            found = self.find_user_by_username(username)
            user_id = found.get("id") if found else None

        if password and user_id:
            self.set_password(user_id, password, temporary=False)

        return {"id": user_id, "username": username}
    


    #Metodo que se llama desde el crear usuario para establecer la contraseña del usuario creado, usando el endpoint de reset-password de Keycloak
    def set_password(self, user_id: str, new_password: str, temporary: bool = False) -> None:
        token = self._get_admin_token()
        url = f"{self._admin_base()}/users/{user_id}/reset-password"
        payload = {"type": "password", "value": new_password, "temporary": temporary}
        headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
        response = requests.put(url, json=payload, headers=headers, timeout=10)
        response.raise_for_status()

    def find_user_by_id(self, user_id: str) -> Optional[Dict[str, Any]]:
        token = self._get_admin_token()
        url = f"{self._admin_base()}/users/{user_id}"   
        headers = {"Authorization": f"Bearer {token}"}
        response = requests.get(url, headers=headers, timeout=10)
        try:
            response.raise_for_status()
        except requests.exceptions.HTTPError as e:
            if response.status_code == 404:
                raise UserNotFoundException(f"User with id {user_id} not found") from e
            raise
        data = response.json()
        # Keycloak returns a single user object for GET /users/{id}.
        # Some code may assume a list; handle both dict and list safely.
        if not data:
            raise UserNotFoundException(f"User with id {user_id} not found")
        if isinstance(data, list):
            return data[0] if data else None
        data["realmRoles"] = self._get_user_realm_roles(user_id)
        return data


    def update_user(self, user_id: str, data: Dict[str, Any]) -> None:
        token = self._get_admin_token()
        url = f"{self._admin_base()}/users/{user_id}"
        headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
        response = requests.put(url, json=data, headers=headers, timeout=10)
        if not response.ok:
            raise RuntimeError(f"Error updating user: {response.status_code} {response.text}")

    def login(self, username: str, password: str) -> Dict[str, Any]:
        data = {"grant_type": "password", "client_id": self.client_id, "username": username, "password": password}
        if self.client_secret:
            data["client_secret"] = self.client_secret
        response = requests.post(self._token_url(), data=data, timeout=10)
        response.raise_for_status()
        return response.json()

    def refresh_token(self, refresh_token: str) -> Dict[str, Any]:
        data = {"grant_type": "refresh_token", "refresh_token": refresh_token}
        if self.client_id:
            data["client_id"] = self.client_id
        if self.client_secret:
            data["client_secret"] = self.client_secret
        response = requests.post(self._token_url(), data=data, timeout=10)
        response.raise_for_status()
        return response.json()

    def validate_token(self, access_token: str) -> Optional[Dict[str, Any]]:
        if not access_token:
            return None
        headers = {"Authorization": f"Bearer {access_token}"}
        try:
            response = requests.get(self._userinfo_url(), headers=headers, timeout=10)
        except requests.exceptions.RequestException:
            return None
        if response.ok:
            return response.json()
        return None

    def change_password(self, user_id: str, new_password: str, temporary: bool = False) -> None:
        self.set_password(user_id, new_password, temporary=temporary)

    def _get_user_realm_roles(self, user_id: str) -> list[str]:
        token = self._get_admin_token()
        url = f"{self._admin_base()}/users/{user_id}/role-mappings/realm"
        headers = {"Authorization": f"Bearer {token}"}
        response = requests.get(url, headers=headers, timeout=10)
        if not response.ok:
            return []
        roles = response.json()
        if not isinstance(roles, list):
            return []
        return [role.get("name") for role in roles if role.get("name")]

    def assign_realm_role(self, user_id: str, role_name: str) -> None:
        token = self._get_admin_token()
        headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}

        role_response = requests.get(self._realm_role_url(role_name), headers=headers, timeout=10)
        if not role_response.ok:
            raise RuntimeError(f"Role not found in realm: {role_name}")

        role_representation = role_response.json()
        url = f"{self._admin_base()}/users/{user_id}/role-mappings/realm"
        response = requests.post(url, json=[role_representation], headers=headers, timeout=10)
        if not response.ok:
            raise RuntimeError(
                f"Error assigning realm role: {response.status_code} {response.text}"
            )
