from abc import ABC, abstractmethod
from typing import Optional, Dict, Any

class IKeycloakService(ABC):
    """Puerto de aplicación para operaciones de usuarios/autenticación en Keycloak."""

    @abstractmethod
    def create_user(
        self,
        username: Optional[str] = None,
        email: Optional[str] = None,
        firstName: Optional[str] = None,
        lastName: Optional[str] = None,
        password: Optional[str] = None,
        attributes: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        raise NotImplementedError()

    @abstractmethod
    def find_user_by_id(self, user_id: str) -> Optional[Dict[str, Any]]:
        raise NotImplementedError()


    @abstractmethod
    def update_user(self, user_id: str, data: Dict[str, Any]) -> None:
        raise NotImplementedError()

    @abstractmethod
    def login(self, username: str, password: str) -> Dict[str, Any]:
        raise NotImplementedError()

    @abstractmethod
    def refresh_token(self, refresh_token: str) -> Dict[str, Any]:
        raise NotImplementedError()

    @abstractmethod
    def change_password(self, user_id: str, new_password: str, temporary: bool = False) -> None:
        raise NotImplementedError()

    @abstractmethod
    def assign_realm_role(self, user_id: str, role_name: str) -> None:
        raise NotImplementedError()

    
