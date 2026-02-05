from Users_Aplication.Commands.RegisterTotpDeviceCommand import RegisterTotpDeviceCommand
from Users_Aplication.DTOs.AuthDTO import TotpRegisterResponseDTO
from Users_Aplication.Interfaces.i_keycloak import IKeycloakService


class RegisterTotpDeviceHandler:
    #Se instancia el servicio de keycloak por inyeccion de dependencias
    def __init__(self, keycloak_service: IKeycloakService):
        self._svc = keycloak_service

    def handle(self, cmd: RegisterTotpDeviceCommand) -> TotpRegisterResponseDTO:
        #El handler recibe el comando RegisterTotpDeviceCommand y retorna un TotpRegisterResponseDTO
        #El comando RegisterTotpDeviceCommand es lo que se va a recibir del frontend
        result = self._svc.register_totp_device(cmd.user_id, cmd.device_name)
        return TotpRegisterResponseDTO(**result)
