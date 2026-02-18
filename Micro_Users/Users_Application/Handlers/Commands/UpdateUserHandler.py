from Users_Application.Commands.UpdateUserCommand import UpdateUserCommand
from Users_Application.DTOs.UserDTO import UserDTO
from Users_Application.Mappers.user_mapper import user_from_keycloak
from Users_Application.Interfaces.i_keycloak import IKeycloakService
from typing import Optional


class UpdateUserHandler:
    """Caso de uso para actualizar datos de un usuario."""

    def __init__(self, keycloak_service: IKeycloakService):
        self._svc = keycloak_service

    def handle(self, cmd: UpdateUserCommand) -> Optional[UserDTO]:
        """Actualiza el usuario y retorna la representación más reciente."""
        payload = cmd.to_payload()
        # actualiza el usuario en keycloak
        self._svc.update_user(cmd.user_id, payload)

        # intenta obtener la representación completa del usuario actualizado
        #Esto es el response que uno ve en fastapi
        user_info = self._svc.find_user_by_id(cmd.user_id)

        if user_info:
            return user_from_keycloak(user_info)

        return None
