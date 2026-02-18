from Users_Application.Commands.RefreshTokenCommand import RefreshTokenCommand
from Users_Application.DTOs.TokenDTO import TokenDTO
from Users_Application.Interfaces.i_keycloak import IKeycloakService


class RefreshTokenHandler:
    """Caso de uso para renovación de access token."""

    def __init__(self, keycloak_service: IKeycloakService):
        self._svc = keycloak_service
    #El handler recibe el comando RefreshTokenCommand y retorna un TokenDTO
    #El comando RefreshTokenCommand es lo que se va a recibir del frontend
    def handle(self, cmd: RefreshTokenCommand) -> TokenDTO:
        """Solicita renovación a Keycloak y retorna `TokenDTO`."""
        token = self._svc.refresh_token(cmd.refresh_token)
        return TokenDTO(**token)
