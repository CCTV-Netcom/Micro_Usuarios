from Users_Aplication.Commands.LoginCommand import LoginCommand
from Users_Aplication.DTOs.TokenDTO import TokenDTO
from Users_Aplication.Interfaces.i_keycloak import IKeycloakService


class LoginHandler:
    #Se instancia el servicio de keycloak por inyeccion de dependencias
    def __init__(self, keycloak_service: IKeycloakService):
        self._svc = keycloak_service

    def handle(self, cmd: LoginCommand) -> TokenDTO:
        #Realiza el login en keycloak y obtiene el token
        #cmd es el comando que contiene username, password y totp
        token = self._svc.login(cmd.username, cmd.password, cmd.totp)
        return TokenDTO(**token)
