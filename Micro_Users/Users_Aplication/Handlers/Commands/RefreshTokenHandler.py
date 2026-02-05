from Users_Aplication.Commands.RefreshTokenCommand import RefreshTokenCommand
from Users_Aplication.DTOs.TokenDTO import TokenDTO
from Users_Aplication.Interfaces.i_keycloak import IKeycloakService


class RefreshTokenHandler:
    #Se instancia el servicio de keycloak por inyeccion de dependencias
    def __init__(self, keycloak_service: IKeycloakService):
        self._svc = keycloak_service
    #El handler recibe el comando RefreshTokenCommand y retorna un TokenDTO
    #El comando RefreshTokenCommand es lo que se va a recibir del frontend
    def handle(self, cmd: RefreshTokenCommand) -> TokenDTO:
        token = self._svc.refresh_token(cmd.refresh_token)
        return TokenDTO(**token)
