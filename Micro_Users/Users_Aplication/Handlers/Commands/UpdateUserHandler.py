from Users_Aplication.Commands.UpdateUserCommand import UpdateUserCommand
from Users_Aplication.DTOs.UserDTO import UserDTO
from Users_Aplication.Mappers.user_mapper import user_from_keycloak
from Users_Aplication.Interfaces.i_keycloak import IKeycloakService
from typing import Optional


class UpdateUserHandler:
    #Se instancia el servicio de keycloak por inyeccion de dependencias
    def __init__(self, keycloak_service: IKeycloakService):
        self._svc = keycloak_service
    #El handler recibe el comando UpdateUserCommand y retorna un UserDTO o None
    def handle(self, cmd: UpdateUserCommand) -> Optional[UserDTO]:
        # Aca llama la funcion de payload del comando para saber que datos actualizar
        payload = cmd.to_payload()
        # actualiza el usuario en keycloak
        self._svc.update_user(cmd.user_id, payload)

        # intenta obtener la representación completa del usuario actualizado
        #Esto es el response que uno ve en fastapi
        #Si no se puede obtener, retorna None
        try:
            user_info = self._svc.find_user_by_id(cmd.user_id)
        except Exception:
            user_info = None

        if user_info:
            return user_from_keycloak(user_info)

        return None
