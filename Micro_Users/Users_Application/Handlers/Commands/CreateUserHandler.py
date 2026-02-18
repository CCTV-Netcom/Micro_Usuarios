from Users_Application.Commands.CreateUserCommand import CreateUserCommand
from Users_Application.DTOs.UserDTO import UserDTO
from Users_Application.Mappers.user_mapper import user_from_keycloak
from Users_Application.Interfaces.i_keycloak import IKeycloakService
from typing import Optional
from pydantic import ValidationError
from Users_Domain.Entities.user import User


class CreateUserHandler:
    """Caso de uso para crear usuarios y asignar rol en Keycloak."""

    def __init__(self, keycloak_service: IKeycloakService):
        self._svc = keycloak_service

    def handle(self, cmd: CreateUserCommand) -> Optional[UserDTO]:
        """Valida datos de dominio, crea usuario y devuelve `UserDTO`."""
        try:
            User(
                email=cmd.email,
                first_name=cmd.first_name,
                last_name=cmd.last_name,
                password=cmd.password,
                cedula=cmd.cedula,
                rol=cmd.rol
            )
        except ValidationError as ve:
            # Propagar la excepción para que el controlador/fastapi la convierta en 422
            raise ve

        attributes = {"Cedula": [str(cmd.cedula)]}
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

        user_info = None
        try:
            user_info = self._svc.find_user_by_id(created.get("id"))
        except Exception:
            user_info = None

        if user_info:
            return user_from_keycloak(user_info)

        # fallback: return minimal
        return UserDTO(id=created.get("id"), username=created.get("username"))
