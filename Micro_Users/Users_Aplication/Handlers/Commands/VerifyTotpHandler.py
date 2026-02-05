from Users_Aplication.Commands.VerifyTotpCommand import VerifyTotpCommand
from Users_Aplication.DTOs.AuthDTO import TotpVerifyResponseDTO
from Users_Aplication.Interfaces.i_keycloak import IKeycloakService


class VerifyTotpHandler:
    #Se instancia el servicio de keycloak por inyeccion de dependencias
    def __init__(self, keycloak_service: IKeycloakService):
        self._svc = keycloak_service

    def handle(self, cmd: VerifyTotpCommand) -> TotpVerifyResponseDTO:
        #El handler recibe el comando VerifyTotpCommand y retorna un TotpVerifyResponseDTO
        #El comando VerifyTotpCommand es lo que se va a recibir de FASTAPI
        result = self._svc.verify_totp(cmd.user_id, cmd.code, getattr(cmd, "secret", None))
        # Retorna el DTO con el resultado de la verificación
        return TotpVerifyResponseDTO(**result)
