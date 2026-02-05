from abc import ABC, abstractmethod
from typing import Optional, Dict, Any

#Esta es la interfaz para interactuar con el servicio de Keycloak
#Es un contrato que debe cumplir cualquier implementacion concreta de Keycloak
#El adaptador de esta puerto debe estar en la capa de infraestructura
class IKeycloakService(ABC):
    @abstractmethod
    def create_user(
        self,
        username: Optional[str] = None,
        email: Optional[str] = None,
        firstName: Optional[str] = None,
        lastName: Optional[str] = None,
        password: Optional[str] = None,
    ) -> Dict[str, Any]:
        raise NotImplementedError()

    @abstractmethod
    def find_user_by_id(self, user_id: str) -> Optional[Dict[str, Any]]:
        raise NotImplementedError()


    @abstractmethod
    def update_user(self, user_id: str, data: Dict[str, Any]) -> None:
        raise NotImplementedError()

    @abstractmethod
    def login(self, username: str, password: str, totp: Optional[str] = None) -> Dict[str, Any]:
        raise NotImplementedError()

    @abstractmethod
    def refresh_token(self, refresh_token: str) -> Dict[str, Any]:
        raise NotImplementedError()

    @abstractmethod
    def change_password(self, user_id: str, new_password: str, temporary: bool = False) -> None:
        raise NotImplementedError()

    @abstractmethod
    def register_totp_device(self, user_id: str, device_name: Optional[str] = None) -> Dict[str, Any]:
        raise NotImplementedError()

    @abstractmethod
    def verify_totp(self, user_id: str, code: str, secret: Optional[str] = None) -> Dict[str, Any]:
        raise NotImplementedError()
