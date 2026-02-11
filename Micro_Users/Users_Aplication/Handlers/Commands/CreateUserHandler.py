from Users_Aplication.Commands.CreateUserCommand import CreateUserCommand
from Users_Aplication.DTOs.UserDTO import UserDTO
from Users_Aplication.Mappers.user_mapper import user_from_keycloak
from Users_Aplication.Interfaces.i_keycloak import IKeycloakService
from typing import Optional


class CreateUserHandler:
    def __init__(self, keycloak_service: IKeycloakService):
        self._svc = keycloak_service

    def handle(self, cmd: CreateUserCommand) -> Optional[UserDTO]:
        attributes = {"Cedula": [str(cmd.cedula)]}
        # crea el usuario en keycloak y obtiene el id generado
        created = self._svc.create_user(
            username=cmd.email,
            email=cmd.email,
            firstName=cmd.first_name,
            lastName=cmd.last_name,
            password=cmd.password,
            attributes=attributes,
        )

        if created.get("id"):
            self._svc.assign_realm_role(created.get("id"), cmd.rol.value)

        # intenta obtener la representación completa del usuario
        #Esto es el response que uno ve en fastapi
        #Si no se puede obtener, retorna un DTO mínimo
        user_info = None
        try:
            user_info = self._svc.find_user_by_id(created.get("id"))
        except Exception:
            user_info = None

        if user_info:
            return user_from_keycloak(user_info)

        # fallback: return minimal
        return UserDTO(id=created.get("id"), username=created.get("username"))
