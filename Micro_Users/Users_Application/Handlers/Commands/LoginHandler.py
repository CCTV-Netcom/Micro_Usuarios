from Users_Application.Commands.LoginCommand import LoginCommand
from Users_Application.DTOs.TokenDTO import TokenDTO
from Users_Application.Interfaces.i_keycloak import IKeycloakService


class LoginHandler:
    """Caso de uso para autenticación por usuario/contraseña."""

    def __init__(self, keycloak_service: IKeycloakService):
        self._svc = keycloak_service

    def handle(self, cmd: LoginCommand) -> TokenDTO:
        """Ejecuta login en Keycloak y mapea el resultado a `TokenDTO`."""
        token = self._svc.login(cmd.username, cmd.password)
        return TokenDTO(**token)
