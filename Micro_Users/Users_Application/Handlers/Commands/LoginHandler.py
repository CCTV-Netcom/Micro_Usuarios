from Users_Application.Commands.LoginCommand import LoginCommand
from Users_Application.DTOs.TokenDTO import TokenDTO
from Users_Application.Interfaces.i_keycloak import IKeycloakService


class LoginHandler:
    #Se instancia el servicio de keycloak por inyeccion de dependencias
    def __init__(self, keycloak_service: IKeycloakService):
        self._svc = keycloak_service

    def handle(self, cmd: LoginCommand) -> TokenDTO:
        #Realiza el login en keycloak y obtiene el token
        #cmd es el comando que contiene username y password
        token = self._svc.login(cmd.username, cmd.password)
        return TokenDTO(**token)
