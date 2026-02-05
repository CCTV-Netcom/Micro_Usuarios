from Users_Aplication.Queries.FindUserByIDQuerie import FindUserByIdQuery
from Users_Aplication.DTOs.UserDTO import UserDTO
from Users_Aplication.Mappers.user_mapper import user_from_keycloak
from Users_Aplication.Interfaces.i_keycloak import IKeycloakService
from typing import Optional
from Users_Domain.Exceptions.exceptions import UserNotFoundException


class FindUserByIdHandler:
    #Se instancia el servicio de keycloak por inyeccion de dependencias
    def __init__(self, keycloak_service: IKeycloakService):
        self._svc = keycloak_service

    def handle(self, query: FindUserByIdQuery) -> Optional[UserDTO]:
        #El handler recibe el comando FindUserByIdQuery y retorna un UserDTO o None
        try:
            user = self._svc.find_user_by_id(query.user_id)
        except UserNotFoundException:
            return None
        if not user:
            return None
        return user_from_keycloak(user)
